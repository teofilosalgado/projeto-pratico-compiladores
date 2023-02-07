from typing import Union
from matplotlib import pyplot as plt
import streamlit as st
import traceback
import networkx as nx
from parsers import LR0

st.set_page_config(layout="wide")

st.title("Projeto Prático de Compiladores")
st.subheader("Aluno: João Victor Teófilo Salgado")
st.caption(
    "Por enquanto, este projeto é apenas capaz de verificar gramáticas perante um "
    "analisador LR(0)."
)

formulario, conteudo_1, conteudo_2 = st.columns([2, 3, 3])
resultado: Union[LR0, None] = None

with formulario:
    st.header("Entrada")
    with st.form("form"):
        gramatica = st.text_area("Gramática")
        variavel_inicial = st.text_input("Símbolo inicial")
        enviar = st.form_submit_button("Enviar")
        if enviar:
            if gramatica and enviar:
                with st.spinner("Carregando..."):
                    try:
                        resultado = LR0(gramatica, variavel_inicial)
                    except Exception:
                        st.error(
                            f"Erro ao processar gramática: {traceback.format_exc()}"
                        )
                if resultado is not None:
                    st.success("Concluído!")
            else:
                st.warning("Por favor, preencha todos os campos.")

    st.write("**Modo de uso:**")
    st.write("Insira gramáticas no seguinte formato: ")
    st.code("S -> A + B\nA -> a\nB -> b")
    st.write(
        "Onde as letras maiúsculas representam variáveis, as setas (->) definem "
        "produções e os outros símbolos são terminais. Não se esqueça de definir o "
        "símbolo inicial, neste caso a letra S, no campo correspondente do "
        "formulário acima. Espaços são opcionais e seram ignorados."
    )

with conteudo_1:
    if resultado is not None:
        rotulos = {
            vertice: f"S{resultado.grafo.nodes[vertice]['indice']}"
            for vertice in resultado.grafo.nodes
        }
        cores = [
            "#66bb6a"
            if resultado.grafo.nodes[vertice]["is_aceitacao"]
            else "#ef5350"
            if resultado.grafo.nodes[vertice]["is_reducao"]
            else "#7986cb"
            for vertice in resultado.grafo.nodes
        ]
        fig, ax = plt.subplots()
        posicao = nx.planar_layout(resultado.grafo)
        nx.draw(
            resultado.grafo,
            posicao,
            labels=rotulos,
            node_color=cores,
            node_size=500,
            node_shape="s",
            with_labels=True,
        )
        nx.draw_networkx_edge_labels(
            resultado.grafo,
            posicao,
            edge_labels=nx.get_edge_attributes(resultado.grafo, "simbolo"),
        )
        st.write("### Grafo")
        st.pyplot(fig)
        st.write("### Validação")
        if resultado.resultado:
            st.success("A gramática é parseável por um analisador LR0.")
        else:
            st.error("A gramática não é parseável por um analisador LR0.")

with conteudo_2:
    if resultado is not None:
        st.write("### Estados")
        st.table(resultado.estados)
        st.write("### Tabela de Transição")
        st.table(resultado.tabela)
