!pip install pyspark
!pip install gcsfs
!pip install pandera
!pip install pymongo[srv]

from pyspark.sql import SparkSession
from pyspark import SparkConf
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType, FloatType

import pandas as pd
import pandera as pa
from google.cloud import storage
import os

import pymongo
from pymongo import MongoClient
import json

from google.colab import drive
drive.mount('/content/drive')

serviceAccount = '/content/drive/MyDrive/************.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = serviceAccount

"""Lendo um arquivo salvo no google cloud plataform e lendo com panda, com uma variavel. Em Seguida Criando uma cópia do mesmo."""

client = storage.Client()

bucket = client.get_bucket('projetoind_gui')
bucket.blob('projetoind_gui/marketing_campaign_final')
path = 'gs://projetoind_gui/marketing_campaign_final/marketing_campaign_'

df = pd.read_csv(path, sep=',')

df_og = df.copy()

client = pymongo.MongoClient("mongodb+srv://*******************************.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

"""Vendo o tipo de cada coluna para uma pré-analise dos dados."""

df.dtypes

"""Definindo quantas colunas o panda deve mostrar e em seguida pedindo para mostrar os 5 primeiros."""

pd.set_option('display.max_columns', 500)
df.head()

"""Vendo se uma certa coluna é única, ou seja se não possuem valores repetidos."""

df.ID.is_unique

"""Vendo quantos valores únicos existem em uma coluna específica."""

sorted(pd.unique(df['Z_CostContact']))

sorted(pd.unique(df['Z_Revenue']))

"""Removendo colunas do dataframe.
Motivos para cada uma da remoções:
Z_CostContact e Z_Revenue, os valores dentro das colunas eram os mesmos em todas as linhas sendo assim desnecessário manter.
AccetedCmp5, AccetedCmp4, AccetedCmp3, AccetedCmp2, AccetedCmp1, Complain e Response, os valores dentros das colunas eram todos booleanos (0 ou 1) e possuam poucos valores '1', além de dependerem diretamente da coluna NumDealsPurchases.
"""

df.drop(['AcceptedCmp5','AcceptedCmp4','AcceptedCmp3','AcceptedCmp2','AcceptedCmp1','Z_CostContact','Z_Revenue','Complain','Response'],axis=1,inplace=True)

"""Renomeando as colunas, fazendo assim que elas fiquem em Português-Br."""

df.rename(columns={'ID':'id','Year_Birth':'ano_nascimento','Education':'escolaridade','Marital_Status':'estado_civil','Income':'renda','Kidhome':'criancas','Teenhome':'adolescente','Dt_Customer':'data_cliente',
'Recency':'recente','MntWines':'qtd_vinhos','MntFruits':'qtd_frutas','MntMeatProducts':'qtd_carne','MntFishProducts':'qtd_peixes','MntSweetProducts':'qtd_doces','MntGoldProds':'qtd_ouro','NumDealsPurchases':'compras_desconto',
'NumWebPurchases':'compras_web','NumCatalogPurchases':'compras_catalogo','NumStorePurchases':'compras_loja','NumWebVisitsMonth':'visitas_web_mes'},inplace=True)

"""Agrupando e somando os valores encontrados na coluna especificada."""

df.groupby(['estado_civil']).estado_civil.count()

"""Corrigindo inconsistencias encontradas em colunas/linhas, mudando seus valores."""

df['estado_civil'] = df['estado_civil'].replace(['Married', 'Together'],'Comprometido')
df['estado_civil'] = df['estado_civil'].replace(['Divorced', 'Widow', 'Alone', 'YOLO', 'Absurd', 'Single'],'Solteiro')

"""Vendo os valores únicos e suas quantidades em uma coluna."""

df.groupby(['escolaridade']).escolaridade.count()

df['escolaridade'] = df['escolaridade'].replace(['2n Cycle'],'Segundo ciclo')
df['escolaridade'] = df['escolaridade'].replace(['Basic'],'Basico')
df['escolaridade'] = df['escolaridade'].replace(['Graduation'],'Graduado')
df['escolaridade'] = df['escolaridade'].replace(['Master'],'Mestrado')
df['escolaridade'] = df['escolaridade'].replace(['PhD'],'Doutorado')

"""Vendo informações de um dataframe."""

df.info()

df.head()

"""Criando um esquema onde os valores dentro de cada coluna são especificados de um tipo de valor e então validando."""

schema = pa.DataFrameSchema(
    columns = {
        "id":pa.Column(pa.Int64),
        "ano_nascimento":pa.Column(pa.Int),
        "escolaridade":pa.Column(pa.String),
        "estado_civil":pa.Column(pa.String),
        "renda":pa.Column(pa.Float,nullable=True),
        "criancas":pa.Column(pa.Int),
        "adolescente":pa.Column(pa.Int),
        "data_cliente":pa.Column(pa.Object),
        "recente":pa.Column(pa.Int),
        "qtd_vinhos":pa.Column(pa.Int),
        "qtd_frutas":pa.Column(pa.Int),
        "qtd_carne":pa.Column(pa.Int),
        "qtd_peixes":pa.Column(pa.Int),
        "qtd_doces":pa.Column(pa.Int),
        "qtd_ouro":pa.Column(pa.Int),
        "compras_desconto":pa.Column(pa.Int),
        "compras_web":pa.Column(pa.Int),
        "compras_catalogo":pa.Column(pa.Int),
        "compras_loja":pa.Column(pa.Int),
        "visitas_web_mes":pa.Column(pa.Int),


    }
)

schema.validate(df)

"""Cópia de um dataframe."""

df2 = df.copy()

"""Configurando o Spark."""

spark = (
    SparkSession.builder
         .master('local')
         .appName('cloudStorage')
         .config('spark.ui.port', '4050')
         .getOrCreate()
)

spark

df_spark = spark.createDataFrame(df2)

df2.head()

"""Estruturando os dados em spark."""

from pyspark.sql.types import StructType
schema = ( StructType ([
   StructField("id", IntegerType(), True),
   StructField("ano_nascimento", IntegerType(), True),
   StructField("escolaridade", StringType(), True),
   StructField("estado_civil", StringType(), True),
   StructField("renda", FloatType(), True),
   StructField("criancas", IntegerType(), True),
   StructField("adolescente", IntegerType(), True),
   StructField("data_cliente", DateType(), True),
   StructField("recente", IntegerType(), True),
   StructField("qtd_vinhos", IntegerType(), True),
   StructField("qtd_frutas", IntegerType(), True),
   StructField("qtd_carne", IntegerType(), True),
   StructField("qtd_peixes", IntegerType(), True),
   StructField("qtd_doces", IntegerType(), True),
   StructField("qtd_ouro", IntegerType(), True),
   StructField("compras_desconto", IntegerType(), True),
   StructField("compras_web", IntegerType(), True),
   StructField("compras_catalogo", IntegerType(), True),
   StructField("compras_loja", IntegerType(), True),
   StructField("visitas_web_mes", IntegerType(), True),     
   ])
)

"""Exibindo o esquema."""

df_spark.printSchema()

df_spark.show()

from pyspark.sql.window import Window

"""Renomeando colunas em spark."""

df_spark = df_spark.withColumnRenamed('qtd_carne', 'qtd_carnes')
df_spark = df_spark.withColumnRenamed('recente', 'ultima_compra_dias')

df_spark.printSchema()

"""Criando uma condição em forma de variável."""

y = Window.partitionBy(F.col('estado_civil')).orderBy('renda')

"""Rankeando e mostarando as linhas a partir de uma condição."""

df_spark.withColumn('dense_rank', F.dense_rank().over(y)).show(20)

"""Adicionando uma coluna somando a partir de outras colunas."""

df3 = df_spark.withColumn("total_criancas_adolescentes", F.col("criancas") + F.col("adolescente"))
df3.filter(F.col("total_criancas_adolescentes") > 1).show(10)

df4 = df3.withColumn("total_compras", F.col("qtd_vinhos") + F.col("qtd_frutas") + F.col("qtd_carnes") + F.col("qtd_peixes") + F.col("qtd_doces") + F.col("qtd_ouro"))
df4.filter(F.col("total_compras") > 100).show(10)

"""Relacionando colunas diferentes.

Vendo a relação entre ano de nascimento e quantidade de vinhos compradas, para saber se a idade é um fator importante para a compra de vinhos.
"""

df4.select(F.col('ano_nascimento'), F.col('qtd_vinhos')).filter(F.col('qtd_vinhos') > 500).show(truncate=False)

"""Relacionando o total de compras com a renda e a escolaridade, para ver se o total de comprar é difetamente influenciado pela renda e essa pela escolaridade."""

df4.select(F.col("total_compras"), F.col('renda'), F.col('escolaridade')).sort(F.col("total_compras").desc()).show(20)

"""Relacionando o ano de nascimento com as compras feitas pela web e por catalogo, para se ver se quanto maior a idade, menor as compras web, tanto em ordem ascendente quanto descendente."""

df4.select(F.col("ano_nascimento"), F.col('compras_web'), F.col('compras_catalogo')).sort(F.col("ano_nascimento").desc()).show(20)

df4.select(F.col("ano_nascimento"), F.col('compras_web'), F.col('compras_catalogo')).sort(F.col("ano_nascimento").asc()).show(20)

"""Relacionando a quantidade de ouro e doce comprados apenas dos que possuem mais de $50.000,00 de renda para ver se aquele com renda alta gastam mais em comprar "desnecessárias"."""

df4.select(F.col('qtd_ouro'), F.col('qtd_doces')).filter(F.col('renda') > 50000.0).show(truncate=False)

df4.select(F.col('qtd_ouro'), F.col('qtd_doces')).filter(F.col('renda') < 50000.0).show(truncate=False)

df4.show()

df4 = spark.read.json("examples/src/main/resources/people.json")
sql.spark('SELECT * FROM ')

db = client['ProjetoInd_Gui']
fn = db.marketing_final

#df4 = df.to_dict("records")
#fn.insertOne(df4)
