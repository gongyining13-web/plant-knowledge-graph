#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from neo4j import GraphDatabase
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jDataImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def test_connection(self):
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("✅ 数据库已清空")
    
    def create_constraints(self):
        constraints = [
            "CREATE CONSTRAINT plant_id_unique IF NOT EXISTS FOR (p:Plant) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT plant_name_unique IF NOT EXISTS FOR (p:Plant) REQUIRE p.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for c in constraints:
                session.run(c)
        logger.info("✅ 约束已创建")
    
    def import_data(self, excel_path):
        # 读取Excel，跳过前5行
        df = pd.read_excel(excel_path, header=5)
        df = df.dropna(subset=['植物中文名']).fillna('')
        logger.info(f"读取到 {len(df)} 条植物数据")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # 创建植物节点
                session.run("""
                    CREATE (p:Plant {
                        id: $id,
                        name: $name,
                        latin_name: $latin_name,
                        family: $family,
                        genus: $genus,
                        distribution: $distribution,
                        folk_use: $folk_use,
                        ecological_meaning: $ecological_meaning,
                        cultural_symbol: $cultural_symbol
                    })
                """, 
                id=row['ID'],
                name=row['植物中文名'],
                latin_name=row['植物拉丁学名'],
                family=row['植物科名'],
                genus=row['植物属名'],
                distribution=row['现代地理分布'],
                folk_use=row['民俗用途'],
                ecological_meaning=row['生态意义'],
                cultural_symbol=row['文化象征'])
                
                # 创建科关系
                if row['植物科名']:
                    session.run("""
                        MATCH (p:Plant {name: $name})
                        MERGE (f:Family {name: $family})
                        MERGE (p)-[:BELONGS_TO_FAMILY]->(f)
                    """, name=row['植物中文名'], family=row['植物科名'])
                
                # 创建象征关系
                if row['文化象征']:
                    for sym in str(row['文化象征']).split('；'):
                        if sym.strip():
                            session.run("""
                                MATCH (p:Plant {name: $name})
                                MERGE (s:Symbol {meaning: $sym})
                                MERGE (p)-[:HAS_SYMBOL]->(s)
                            """, name=row['植物中文名'], sym=sym.strip())
                
                logger.info(f"导入: {row['植物中文名']}")
        
        logger.info("🎉 数据导入完成")

def main():
    importer = Neo4jDataImporter(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="12345678"
    )
    
    if importer.test_connection():
        # 请根据实际情况修改Excel路径
        excel_path = "data/荆楚植物文化图谱植物数据.xlsx"
        if not os.path.exists(excel_path):
            logger.error(f"文件不存在: {excel_path}")
            return
        
        confirm = input("是否清空数据库？(y/N): ")
        if confirm.lower() == 'y':
            importer.clear_database()
        
        importer.create_constraints()
        importer.import_data(excel_path)
    
    importer.close()

if __name__ == "__main__":
    main()