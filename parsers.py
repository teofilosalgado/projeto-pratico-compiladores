import re
from typing import List, Set
from networkx import DiGraph, set_node_attributes
import pandas as pd


class LR0:
    def obter_variaveis(self, producoes: str) -> Set[str]:
        return set(re.findall("[A-Z]", producoes, re.MULTILINE))

    def obter_terminais(self, producoes: str) -> List[str]:
        return [*sorted([*set(re.findall("[^A-Z→\n]", producoes, re.MULTILINE))]), "$"]

    def obter_simbolos_pendentes(self, producoes: str) -> Set[str]:
        return set(re.findall("·(.)", producoes, re.MULTILINE))

    def obter_variaveis_pendentes(self, producoes: str) -> Set[str]:
        return set(re.findall("·([A-Z])", producoes, re.MULTILINE))

    def obter_producoes_by_variavel(self, producoes: str, variavel: str) -> Set[str]:
        return set(re.findall(f"^{re.escape(variavel)}→.+$", producoes, re.MULTILINE))

    def obter_producoes_by_simbolo(self, producoes: str, simbolo: str) -> Set[str]:
        return set(
            re.findall(f"^.+→.*·{re.escape(simbolo)}.*$", producoes, re.MULTILINE)
        )

    def obter_estado_inicial_auxiliar(
        self, producoes: str, variavel: str, variaveis_analisadas: Set[str]
    ) -> str:
        novas_variaveis_analisadas = set([*variaveis_analisadas, variavel])
        novas_producoes = re.sub(
            f"({re.escape(variavel)}→)(.+)", r"\1·\2", producoes, flags=re.MULTILINE
        )
        variaveis_pendentes = (
            self.obter_variaveis_pendentes(novas_producoes) - novas_variaveis_analisadas
        )
        if variaveis_pendentes:
            return self.obter_estado_inicial_auxiliar(
                novas_producoes,
                next(iter(variaveis_pendentes)),
                novas_variaveis_analisadas,
            )
        else:
            return novas_producoes

    def obter_estado_inicial(self, producoes: str, variavel: str) -> str:
        return self.obter_estado_inicial_auxiliar(producoes, variavel, set([]))

    def fechamento_auxiliar(
        self, estado_inicial: str, estado_atual: str, variaveis_analisadas: Set[str]
    ) -> str:
        variaveis_pendentes_fechamentos = (
            self.obter_variaveis_pendentes(estado_atual) - variaveis_analisadas
        )
        if variaveis_pendentes_fechamentos:
            variavel = next(iter(variaveis_pendentes_fechamentos))
            novas_variaveis_analisadas = set([*variaveis_analisadas, variavel])
            producoes_fechamentos = "\n".join(
                self.obter_producoes_by_variavel(estado_inicial, variavel)
            )
            novo_estado_atual = f"{estado_atual}\n{producoes_fechamentos}"
            return self.fechamento_auxiliar(
                estado_inicial, novo_estado_atual, novas_variaveis_analisadas
            )
        else:
            return estado_atual

    def fechamento(self, estado_inicial: str, estado_atual: str) -> str:
        return self.fechamento_auxiliar(estado_inicial, estado_atual, set([]))

    def simular_leitura(self, estado_inicial: str, estado_atual: str, variavel: str):
        producoes_afetadas = self.obter_producoes_by_simbolo(estado_atual, variavel)
        producoes_afetadas_atualizadas = "\n".join(
            [
                re.sub(
                    f"·{re.escape(variavel)}",
                    f"{variavel}·",
                    producao,
                    flags=re.MULTILINE,
                )
                for producao in producoes_afetadas
            ]
        )
        return self.fechamento(estado_inicial, producoes_afetadas_atualizadas)

    def percorrer_estados_auxiliar(
        self, estado_inicial: str, estado_atual: str, resultado: DiGraph
    ):
        simbolos_pendentes = self.obter_simbolos_pendentes(estado_atual)
        for simbolo in simbolos_pendentes:
            proximo_estado = self.simular_leitura(estado_inicial, estado_atual, simbolo)
            if proximo_estado not in resultado.nodes:
                is_aceitacao = True if "'" in proximo_estado else False
                atributos = {}
                reducao = re.findall("(.)·$", proximo_estado, re.MULTILINE)
                if reducao and not is_aceitacao:
                    atributos["is_reducao"] = True
                    atributos["reducao"] = ",".join(reducao)
                else:
                    atributos["is_reducao"] = False
                    atributos["reducao"] = None
                resultado.add_node(
                    proximo_estado,
                    is_aceitacao=is_aceitacao,
                    indice_reducao=None,
                    **atributos,
                )
                resultado.add_edge(estado_atual, proximo_estado, simbolo=simbolo)
                self.percorrer_estados_auxiliar(
                    estado_inicial, proximo_estado, resultado
                )

    def percorrer_estados(self, entrada: str, variavel_inicial: str):
        estado_inicial = self.obter_estado_inicial(entrada, variavel_inicial)
        resultado = DiGraph()
        resultado.add_node(
            estado_inicial,
            is_aceitacao=False,
            is_reducao=False,
            indice_reducao=None,
            reducao=None,
        )
        self.percorrer_estados_auxiliar(estado_inicial, estado_inicial, resultado)
        indices = {
            estado: indice for indice, estado in enumerate(list(resultado.nodes))
        }
        indices_reducoes = {
            estado: f"{indice}"
            for indice, estado in enumerate(
                [
                    item
                    for item in resultado.nodes
                    if resultado.nodes[item]["is_reducao"]
                ]
            )
        }
        set_node_attributes(resultado, indices, "indice")
        set_node_attributes(resultado, indices_reducoes, "indice_reducao")
        return resultado

    def __init__(self, entrada: str, variavel_inicial: str) -> None:
        # Processa a entrada
        nova_variavel_inicial = f"{variavel_inicial}'"
        entrada_normalizada = entrada.replace(" ", "").replace("->", "→")
        entrada_parseada = (
            f"{nova_variavel_inicial}→{variavel_inicial}\n{entrada_normalizada}"
        )
        variaveis = self.obter_variaveis(entrada_normalizada)
        terminais = self.obter_terminais(entrada_normalizada)

        # Gera o grafo de estados
        grafo = self.percorrer_estados(entrada_parseada, nova_variavel_inicial)

        # Gera a leganda de estados do grafo
        estados = pd.DataFrame.from_records(
            [{"estado": item, **grafo.nodes[item]} for item in grafo.nodes],
            index="indice",
        ).drop("reducao", axis=1)
        lookup = {"True": "✔️", "False": ""}
        estados["is_reducao"] = estados["is_reducao"].astype(str).map(lookup)
        estados["is_aceitacao"] = estados["is_aceitacao"].astype(str).map(lookup)
        estados["indice_reducao"] = estados["indice_reducao"].fillna("")
        estados.columns = ["Estado", "Aceitação?", "Redução?", "N.° da Redução"]

        # Gera a tabela de estados
        tabela_estados_base = [
            {
                "indice": item,
                **{terminal: [] for terminal in terminais},
                **{variavel: [] for variavel in variaveis},
            }
            for item in [grafo.nodes[item]["indice"] for item in grafo.nodes]
        ]
        for estado in [
            grafo.nodes[item]["indice"]
            for item in grafo.nodes
            if grafo.nodes[item]["is_aceitacao"]
        ]:
            tabela_estados_base[estado]["$"].append("ACC")
        for estado, linha in enumerate(tabela_estados_base):
            vertice = next(
                item for item in grafo.nodes if grafo.nodes[item]["indice"] == estado
            )
            simbolos_destinos = [
                (atributos["simbolo"], grafo.nodes[destino]["indice"])
                for origem, destino, atributos in grafo.edges(data=True)
                if origem == vertice
            ]
            for simbolo, destino in simbolos_destinos:
                if simbolo.isupper():
                    tabela_estados_base[estado][simbolo].append(f"{destino}")
                else:
                    tabela_estados_base[estado][simbolo].append(f"S{destino}")
        reducoes_indices = [
            (grafo.nodes[item]["indice"], grafo.nodes[item]["indice_reducao"])
            for item in grafo.nodes
            if grafo.nodes[item]["is_reducao"]
        ]
        for indice, indice_reducao in reducoes_indices:
            for terminal in terminais:
                tabela_estados_base[indice][terminal].append(f"R{indice_reducao}")

        # Verifica se a gramatica é LR0 e gera o dataframe final
        resultado = True
        for linha in range(len(tabela_estados_base)):
            for coluna in [*terminais, *variaveis]:
                # Verifica se encontrou conflito, caso positivo, não é LR0
                if len(tabela_estados_base[linha][coluna]) > 1:
                    resultado = False
                tabela_estados_base[linha][coluna] = ", ".join(
                    tabela_estados_base[linha][coluna]
                )
        tabela = pd.DataFrame.from_records(
            tabela_estados_base, index="indice"
        ).rename_axis(None)

        # Define os resultados como campos na classe
        self.grafo = grafo
        self.estados = estados
        self.tabela = tabela
        self.resultado = resultado
