from flask import Flask, make_response,jsonify, request
from db import engine, tabela_clientes, tabela_produtos, tabela_contratos, tabela_resgates, tabela_aportes
from datetime import datetime, date, timedelta 

connect = engine.connect()



app = Flask(__name__)

#Rota de cadastramento de clientes
@app.route("/cadclientes", methods=["POST"])
def cadCliente():
    cliente = request.json
    tabela_clientes.insert().values(
        cpf=cliente["cpf"],
        nome=cliente["nome"],
        dataDeNascimento=datetime.strptime(cliente["dataDeNascimento"],'%Y-%m-%d'),
        sexo=cliente["sexo"],
        rendaMensal=cliente["rendaMensal"]
        ).execute()
    return make_response(
        jsonify(
            {
                "id": tabela_clientes.select().where(tabela_clientes.c.cpf == cliente["cpf"]).execute().fetchone()[0]
            }
        )
    )

#Rota de cadastramento de produtos
@app.route("/cadprodutos", methods=["POST"])
def cadProduto():
    produto = request.json
    tabela_produtos.insert().values(
        nome=produto["nome"],
        susep=produto["susep"],
        expiracaoDeVenda=datetime.strptime(produto["expiracaoDeVenda"],'%Y-%m-%d'),
        valorMinimoAporteInicial=produto["valorMinimoAporteInicial"],
        valorMinimoAporteExtra=produto["valorMinimoAporteExtra"],
        idadeDeEntrada=produto["idadeDeEntrada"],
        idadeDeSaida=produto["idadeDeSaida"],
        carenciaInicialDeResgate=produto["carenciaInicialDeResgate"],
        carenciaEntreResgates=produto["carenciaEntreResgates"]
        ).execute()
    return make_response(
        jsonify(
            {
                "id": tabela_produtos.select().where(tabela_produtos.c.susep == produto["susep"]).execute().fetchone()[0]
            }
        )
    )
#Rota de cadastramento de contratos

#REGRAS DE NEGÓCIO
#1 - Não pode cadastrar um contrato com um produto expirado
#2 - Não pode cadastrar um contrato com um cliente fora da faixa etária (idadeDeEntrada e idadeDeSaida)
#3 - Não pode cadastrar um contrato com um aporte inicial menor que o valor mínimo (valorMinimoAporteInicial)

@app.route("/cadcontratos", methods=["POST"])
def cadContrato():
    contrato = request.json
    produtos = listProdutos()
    for produto in produtos:
        if produto["id"] == contrato["idProduto"]:
            #Caso o produto esteja expirado
            if datetime.strptime(produto["expiracaoDeVenda"],'%Y-%m-%d') < datetime.strptime(contrato["dataDaContratacao"],'%Y-%m-%d'):
                return make_response(
                    jsonify(
                        {
                            "erro": "Produto expirado"
                        }
                    )
                )
            #Caso o produto não esteja expirado e o aporte seja maior que o valor mínimo    
            if datetime.strptime(produto["expiracaoDeVenda"],'%Y-%m-%d') > datetime.strptime(contrato["dataDaContratacao"],'%Y-%m-%d'):
                if produto["valorMinimoAporteInicial"] > contrato["aporte"]:
                    return make_response(
                        jsonify(
                            {
                                "erro": "Aporte inicial menor que o mínimo"
                            }
                        )
                    )
                #Caso o produto não esteja expirado e o aporte seja maior que o valor mínimo e o cliente esteja dentro da faixa etária
                if produto["valorMinimoAporteInicial"] < contrato["aporte"]:
                    listaClientes = listClientes()
                    for cliente in listaClientes:
                        if cliente["id"] == contrato["idCliente"]:
                            #Caso o cliente esteja dentro da faixa etária
                            if date.today().year - datetime.strptime(cliente["dataDeNascimento"],'%Y-%m-%d').year > produto["idadeDeEntrada"] and date.today().year - datetime.strptime(cliente["dataDeNascimento"],'%Y-%m-%d').year < produto["idadeDeSaida"]: 
                                tabela_contratos.insert().values(
                                    idCliente=contrato["idCliente"],
                                    idProduto=contrato["idProduto"],
                                    dataDaContratacao=datetime.strptime(contrato["dataDaContratacao"],'%Y-%m-%d'),
                                    aporte=contrato["aporte"]
                                    ).execute()
                                return make_response(
                                    jsonify(
                                        {
                                            "id": tabela_contratos.select().where(tabela_contratos.c.idCliente == contrato["idCliente"]).execute().fetchone()[0]
                                        }
                                    )
                                )
                            else:
                                return make_response(
                                    jsonify(
                                        {
                                            "erro": "Cliente fora da faixa etária"
                                        }
                                    )
                                )

#Rota de cadastramento de resgates
#REGRAS DE NEGÓCIO
#1 - Não pode cadastrar um resgate com a carencia inicial de resgate não cumprida
#2 - Não pode cadastrar um resgate com a carencia entre resgates não cumprida
#3 - Não pode cadastrar um resgate com um valor maior que o saldo do contrato


@app.route("/cadresgates", methods=["POST"])
def cadResgate():
    resgate = request.json
    listaContratos = listContratos()
    listaProdutos = listProdutos()
    for produto in listaProdutos:
        if produto["id"] == resgate["idPlano"]:
            for contrato in listaContratos:
                if contrato["id"] == resgate["idPlano"]:
                    #Caso a carencia inicial de resgate não esteja cumprida
                    if contrato["dataDaContratacao"] + timedelta(days=produto["carenciaInicialDeResgate"]) > date.today():
                        return make_response(
                            jsonify(
                                {
                                    "erro": "Carencia inicial de resgate não cumprida"
                                }
                            )
                        )
                    #Caso a carencia entre resgates não esteja cumprida
                    if contrato["dataDaContratacao"] + timedelta(days=produto["carenciaEntreResgates"]) > date.today():
                        return make_response(
                            jsonify(
                                {
                                    "erro": "Carencia entre resgates não cumprida"
                                }
                            )
                        )
                    #Caso a carencia entre resgates esteja cumprida e o valor do resgate seja maior que o saldo do contrato
                    if contrato["dataDaContratacao"] + timedelta(days=produto["carenciaEntreResgates"]) < date.today():
                        #Caso o valor do resgate seja maior que o saldo do contrato
                        if resgate["valorResgate"] > contrato["aporte"]:
                            return make_response(
                                jsonify(
                                    {
                                        "erro": "Valor de resgate maior que o aporte"
                                    }
                                )
                            )
                        #Caso o valor do resgate seja menor que o saldo do contrato
                        if resgate["valorResgate"] < contrato["aporte"]:
                            tabela_resgates.insert().values(
                                idPlano=resgate["idPlano"],
                                valorResgate=resgate["valorResgate"]
                                ).execute()
                            #Atualiza o saldo do contrato
                            tabela_contratos.update().where(tabela_contratos.c.idCliente == produto['idCliente']).values(
                                aporte=contrato["aporte"] - resgate["valorResgate"]).execute()
                            return make_response(
                                jsonify(
                                    {
                                        "id": tabela_resgates.select().where(tabela_resgates.c.idPlano == resgate["idPlano"]).execute().fetchone()[0]
                                    }
                                )
                            )
#Rota de cadastramento de aportes extras
# REGRAS DE NEGÓCIO
# 1 - Não pode cadastrar um aporte extra com um valor menor que o valor minimo de aporte extra
                            

@app.route("/cadaportes", methods=["POST"])
def cadAporte():
    aporte = request.json
    listaProdutos = listProdutos()
    for produto in listaProdutos:
        if produto["id"] == aporte["idPlano"]:
            #Caso o valor do aporte extra seja menor que o valor minimo de aporte extra
            if produto["valorMinimoAporteExtra"] > aporte["valorAporte"]:
                return make_response(
                    jsonify(
                        {
                            "erro": "Aporte extra menor que o mínimo"
                        }
                    )
                )
            #Caso o valor do aporte extra seja maior que o valor minimo de aporte extra
            if produto["valorMinimoAporteExtra"] < aporte["valorAporte"]:

                tabela_aportes.insert().values(
                    idCliente=aporte["idCliente"],
                    idPlano=aporte["idPlano"],
                    valorAporte=aporte["valorAporte"]
                    ).execute()
                #Atualiza o valor do aporte do contrato    
                tabela_contratos.update().where(tabela_contratos.c.idCliente == aporte["idCliente"]).values(aporte=tabela_contratos.c.aporte + aporte["valorAporte"]).execute()
                return make_response(
                    jsonify(
                        {
                            "id": tabela_aportes.select().where(tabela_aportes.c.idCliente == aporte["idCliente"]).execute().fetchone()[0]
                        }
                    )
                )

#Rota de listagem de clientes
@app.route("/listaclientes", methods=["GET"])
def listClientes():
    clientes = []
    for cliente in connect.execute(tabela_clientes.select()):
        clientes.append({
            "id": cliente[0],
            "cpf": cliente[1],
            "nome": cliente[2],
            "dataDeNascimento": cliente[3].strftime('%Y-%m-%d'),
            "sexo": cliente[4],
            "rendaMensal": cliente[5]
        })
    return make_response(
        jsonify(
            clientes
        )

    )

#Rota de listagem de produtos
@app.route("/listaprodutos", methods=["GET"])
def listProdutos():
    produtos = []
    for produto in connect.execute(tabela_produtos.select()):
        produtos.append({
            "id": produto[0],
            "nome": produto[1],
            "susep": produto[2],
            "expiracaoDeVenda": produto[3].strftime('%Y-%m-%d'),
            "valorMinimoAporteInicial": produto[4],
            "valorMinimoAporteExtra": produto[5],
            "idadeDeEntrada": produto[6],
            "idadeDeSaida": produto[7],
            "carenciaInicialDeResgate": produto[8],
            "carenciaEntreResgates": produto[9]
        })
    return make_response(
        jsonify(
            produtos
        )

    )

#Rota de listagem de contratos
@app.route("/listacontratos", methods=["GET"])
def listContratos():
    contratos = []
    for contrato in connect.execute(tabela_contratos.select()):
        contratos.append({
            "id": contrato[0],
            "idCliente": contrato[1],
            "idProduto": contrato[2],
            "dataDaContratacao": contrato[3].strftime('%Y-%m-%d'),
            "aporte": contrato[4]
        })
    return make_response(
        jsonify(
            contratos
        )

    )

#Rota de listagem de resgates
@app.route("/listaresgates", methods=["GET"])
def listResgates():
    resgates = []
    for resgate in connect.execute(tabela_resgates.select()):
        resgates.append({
            "id": resgate[0],
            "idPlano": resgate[1],
            "valorResgate": resgate[2]
        })
    return make_response(
        jsonify(
            resgates
        )

    )

#Rota de listagem de aportes
@app.route("/listaaportes", methods=["GET"])
def listAportes():
    aportes = []
    for aporte in connect.execute(tabela_aportes.select()):
        aportes.append({
            "id": aporte[0],
            "idCliente": aporte[1],
            "idPlano": aporte[2],
            "valorAporte": aporte[3]
        })
    return make_response(
        jsonify(
            aportes
        )

    )             



app.run(debug=True)