#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荆楚植物文化图谱 - Neo4j 数据导入脚本（云数据库版）
将 Excel 数据导入到 Neo4j AuraDB
"""

import pandas as pd
from neo4j import GraphDatabase
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jDataImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"✅ 连接至 {uri}")
        
    def close(self):
        self.driver.close()
        
    def test_connection(self):
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败: {e}")
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
                try:
                    session.run(c)
                except Exception as e:
                    logger.warning(f"约束可能已存在: {e}")
        logger.info("✅ 约束已创建")
    
    def import_data(self, excel_path):
        # 读取 Excel，跳过前5行标题
        df = pd.read_excel(excel_path, header=5)
        df = df.dropna(subset=['植物中文名']).fillna('')
        logger.info(f"📊 读取到 {len(df)} 条植物数据")
        
        with self.driver.session() as session:
            for index, row in df.iterrows():
                try:
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
                            cultural_symbol: $cultural_symbol,
                            medicinal_value: $medicinal_value,
                            literature_source: $literature_source,
                            festival: $festival
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
                    cultural_symbol=row['文化象征'],
                    medicinal_value=row['药用价值'],
                    literature_source=row['文献出处'],
                    festival=row['节日'])
                    
                    # 创建科关系
                    if row['植物科名']:
                        session.run("""
                            MATCH (p:Plant {name: $name})
                            MERGE (f:Family {name: $family})
                            MERGE (p)-[:BELONGS_TO_FAMILY]->(f)
                        """, name=row['植物中文名'], family=row['植物科名'])
                    
                    # 创建象征意义关系
                    if row['文化象征']:
                        symbols = str(row['文化象征']).split('；')
                        for sym in symbols:
                            if sym.strip():
                                session.run("""
                                    MATCH (p:Plant {name: $name})
                                    MERGE (s:Symbol {meaning: $sym})
                                    MERGE (p)-[:HAS_SYMBOL]->(s)
                                """, name=row['植物中文名'], sym=sym.strip())
                    
                    # 创建药用价值关系
                    if row['药用价值'] and row['药用价值'] != '无药用记载':
                        medicines = str(row['药用价值']).replace('；', ',').split(',')
                        for med in medicines:
                            if med.strip():
                                session.run("""
                                    MATCH (p:Plant {name: $name})
                                    MERGE (m:Medicinal {effect: $med})
                                    MERGE (p)-[:HAS_MEDICINAL]->(m)
                                """, name=row['植物中文名'], med=med.strip())
                    
                    # 创建文献关系
                    if row['文献出处']:
                        session.run("""
                            MATCH (p:Plant {name: $name})
                            MERGE (l:Literature {name: $lit})
                            MERGE (p)-[:RECORDED_IN]->(l)
                        """, name=row['植物中文名'], lit=row['文献出处'])
                    
                    # 创建节日关系
                    if row['节日']:
                        festivals = str(row['节日']).split('；')
                        for f in festivals:
                            if f.strip():
                                session.run("""
                                    MATCH (p:Plant {name: $name})
                                    MERGE (f:Festival {name: $fest})
                                    MERGE (p)-[:RELATED_TO_FESTIVAL]->(f)
                                """, name=row['植物中文名'], fest=f.strip())
                    
                    logger.info(f"✅ 已导入: {row['植物中文名']} ({index+1}/{len(df)})")
                    
                except Exception as e:
                    logger.error(f"❌ 导入失败 {row.get('植物中文名', '未知')}: {e}")
        
        logger.info("🎉 数据导入完成！")
    
    def get_statistics(self):
        stats = {}
        with self.driver.session() as session:
            stats['植物总数'] = session.run("MATCH (p:Plant) RETURN count(p) as c").single()['c']
            stats['科的数量'] = session.run("MATCH (f:Family) RETURN count(f) as c").single()['c']
            stats['象征意义数量'] = session.run("MATCH (s:Symbol) RETURN count(s) as c").single()['c']
            stats['药用价值数量'] = session.run("MATCH (m:Medicinal) RETURN count(m) as c").single()['c']
            stats['文献数量'] = session.run("MATCH (l:Literature) RETURN count(l) as c").single()['c']
            stats['节日数量'] = session.run("MATCH (f:Festival) RETURN count(f) as c").single()['c']
        return stats


def main():
    # ========== 云数据库连接信息（已填好，可直接使用） ==========
   NEO4J_URI = "bolt://localhost:7687"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "12345678"
    
    # Excel 文件路径（相对于项目根目录）
    EXCEL_PATH = "data/荆楚植物文化图谱植物数据.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"❌ 找不到 Excel 文件: {os.path.abspath(EXCEL_PATH)}")
        logger.error("请将 Excel 文件放在 data 文件夹下，并命名为：荆楚植物文化图谱植物数据.xlsx")
        return
    
    # 创建导入器实例
    importer = Neo4jDataImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # 测试连接
        if not importer.test_connection():
            logger.error("❌ 无法连接到 Neo4j 数据库，请检查网络和连接信息")
            return
        
        # 是否清空数据库
        confirm = input("⚠️ 是否清空数据库？(y/N): ")
        if confirm.lower() == 'y':
            importer.clear_database()
        
        # 创建约束
        importer.create_constraints()
        
        # 导入数据
        importer.import_data(EXCEL_PATH)
        
        # 显示统计信息
        logger.info("📊 数据库统计信息:")
        stats = importer.get_statistics()
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ 导入过程中出错: {e}")
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()