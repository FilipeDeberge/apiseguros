from sqlalchemy import(create_engine, Column, Integer, String, Date, Float, MetaData, Table)

engine = create_engine('sqlite:///banco.db', echo=True)
metadata = MetaData(bind=engine)

tabela_clientes = Table('tb_clientes', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('cpf', String(11), unique=True),
    Column('nome', String(255)),
    Column('dataDeNascimento', Date),
    Column('sexo', String(1)),
    Column('rendaMensal', Float))

tabela_produtos = Table('tb_produtos', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('nome', String(255)),
    Column('susep', String(255)),
    Column('expiracaoDeVenda', Date),
    Column('valorMinimoAporteInicial', Float),
    Column('valorMinimoAporteExtra', Float),
    Column('idadeDeEntrada', Integer),
    Column('idadeDeSaida', Integer),
    Column('carenciaInicialDeResgate', Integer),
    Column('carenciaEntreResgates', Integer))

tabela_contratos = Table('tb_contratos', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('idCliente', Integer),
    Column('idProduto', Integer),
    Column('dataDaContratacao', Date),
    Column('aporte', Float))

tabela_resgates = Table('tb_resgates', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('idPlano', Integer),
    Column('valorResgate', Float))
    
tabela_aportes = Table('tb_aportes', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('idCliente', Integer),
    Column('idPlano', Integer),
    Column('valorAporte', Float))


metadata.create_all()