const elementos = {
    busca: document.getElementById("busca-jogador"),
    filtroTime: document.getElementById("filtro-time"),
    lista: document.getElementById("lista-jogadores"),
    status: document.getElementById("status-texto"),
    total: document.getElementById("total-jogadores"),
    semResultados: document.getElementById("sem-resultados"),
    template: document.getElementById("template-jogador")
};

let jogadores = [];

document.addEventListener("DOMContentLoaded", iniciar);

async function iniciar() {
    configurarEventos();
    await carregarDados();
}


/* =========================
   CARREGAMENTO
========================= */

async function carregarDados() {
    atualizarStatus("Carregando jogadores...");

    try {
        const resposta = await fetch("./dados.csv", {
            cache: "no-store"
        });

        if (!resposta.ok) {
            throw new Error(
                `Erro ao carregar dados.csv: ${resposta.status}`
            );
        }

        const texto = await resposta.text();

        const separador = detectarSeparador(texto);
        const linhas = parseCSV(texto, separador);

        if (linhas.length < 2) {
            throw new Error("dados.csv não possui registros.");
        }

        jogadores = agruparJogadores(linhas);

        if (jogadores.length === 0) {
            throw new Error(
                "Nenhum jogador pôde ser criado a partir do CSV."
            );
        }

        preencherFiltroTimes();
        aplicarFiltros();

    } catch (erro) {
        console.error("Erro ao carregar dados:", erro);

        jogadores = [];
        elementos.lista.innerHTML = "";
        elementos.total.textContent = "0";
        elementos.semResultados.hidden = false;

        atualizarStatus(
            "Não foi possível carregar os dados dos jogadores."
        );
    }
}


/* =========================
   DETECÇÃO DO SEPARADOR
========================= */

function detectarSeparador(texto) {
    const primeiraLinha =
        texto.split(/\r?\n/)[0] || "";

    const quantidadePontoVirgula =
        (primeiraLinha.match(/;/g) || []).length;

    const quantidadeVirgula =
        (primeiraLinha.match(/,/g) || []).length;

    return quantidadePontoVirgula > quantidadeVirgula
        ? ";"
        : ",";
}


/* =========================
   LEITOR CSV
========================= */

function parseCSV(texto, separador) {
    const linhas = [];

    let linha = [];
    let campo = "";
    let dentroAspas = false;

    for (let i = 0; i < texto.length; i++) {
        const caractere = texto[i];

        if (caractere === '"') {

            if (
                dentroAspas &&
                texto[i + 1] === '"'
            ) {
                campo += '"';
                i++;
            } else {
                dentroAspas = !dentroAspas;
            }

        } else if (
            caractere === separador &&
            !dentroAspas
        ) {

            linha.push(campo);
            campo = "";

        } else if (
            (
                caractere === "\n" ||
                caractere === "\r"
            ) &&
            !dentroAspas
        ) {

            if (
                caractere === "\r" &&
                texto[i + 1] === "\n"
            ) {
                i++;
            }

            linha.push(campo);

            if (
                linha.some(
                    valor =>
                        String(valor).trim() !== ""
                )
            ) {
                linhas.push(linha);
            }

            linha = [];
            campo = "";

        } else {

            campo += caractere;

        }
    }

    if (
        campo.length > 0 ||
        linha.length > 0
    ) {

        linha.push(campo);

        if (
            linha.some(
                valor =>
                    String(valor).trim() !== ""
            )
        ) {
            linhas.push(linha);
        }
    }

    return linhas;
}


/* =========================
   AGRUPAR JOGADORES
========================= */

function agruparJogadores(linhas) {

    const cabecalhos =
        linhas[0].map(
            cabecalho =>
                String(cabecalho)
                    .replace(/^\uFEFF/, "")
                    .trim()
                    .toLowerCase()
        );

    const indice = {};

    cabecalhos.forEach(
        (nome, posicao) => {
            indice[nome] = posicao;
        }
    );

    const obrigatorias = [
        "nome",
        "time",
        "data",
        "adversario",
        "pts",
        "reb",
        "ast",
        "tpm",
        "stl",
        "blk"
    ];

    const faltando =
        obrigatorias.filter(
            coluna =>
                indice[coluna] === undefined
        );

    if (faltando.length > 0) {
        throw new Error(
            "Colunas ausentes: " +
            faltando.join(", ")
        );
    }

    const mapa = new Map();

    linhas.slice(1).forEach(colunas => {

        const nome =
            valorCSV(
                colunas,
                indice.nome
            );

        if (!nome) {
            return;
        }

        const time =
            valorCSV(
                colunas,
                indice.time
            );

        if (!mapa.has(nome)) {

            mapa.set(
                nome,
                {
                    nome,
                    time,
                    jogos: []
                }
            );
        }

        mapa.get(nome).jogos.push({

            data:
                valorCSV(
                    colunas,
                    indice.data
                ),

            adversario:
                valorCSV(
                    colunas,
                    indice.adversario
                ),

            casa_fora:
                valorCSV(
                    colunas,
                    indice.casa_fora
                ),

            minutos:
                numeroCSV(
                    colunas,
                    indice.minutos
                ),

            pts:
                numeroCSV(
                    colunas,
                    indice.pts
                ),

            reb:
                numeroCSV(
                    colunas,
                    indice.reb
                ),

            ast:
                numeroCSV(
                    colunas,
                    indice.ast
                ),

            tpm:
                numeroCSV(
                    colunas,
                    indice.tpm
                ),

            stl:
                numeroCSV(
                    colunas,
                    indice.stl
                ),

            blk:
                numeroCSV(
                    colunas,
                    indice.blk
                )
        });
    });

    return Array.from(mapa.values())
        .map(jogador => ({
            ...jogador,

            jogos:
                ordenarJogos(
                    jogador.jogos
                ).slice(0, 10)
        }))
        .sort(
            (a, b) =>
                a.nome.localeCompare(
                    b.nome,
                    "pt-BR"
                )
        );
}


/* =========================
   VALORES CSV
========================= */

function valorCSV(colunas, posicao) {

    if (posicao === undefined) {
        return "";
    }

    return String(
        colunas[posicao] ?? ""
    ).trim();
}


function numeroCSV(colunas, posicao) {

    const valor =
        valorCSV(
            colunas,
            posicao
        );

    if (valor === "") {
        return null;
    }

    const numero =
        Number(
            valor
                .replace(/\s/g, "")
                .replace(",", ".")
        );

    return Number.isFinite(numero)
        ? numero
        : null;
}


/* =========================
   DATAS
========================= */

function converterData(valor) {

    if (!valor) {
        return null;
    }

    const texto =
        String(valor).trim();

    let data =
        new Date(texto);

    if (
        !Number.isNaN(
            data.getTime()
        )
    ) {
        return data;
    }

    const partes =
        texto.match(
            /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/
        );

    if (partes) {

        data = new Date(
            Number(partes[3]),
            Number(partes[2]) - 1,
            Number(partes[1])
        );

        if (
            !Number.isNaN(
                data.getTime()
            )
        ) {
            return data;
        }
    }

    return null;
}


function ordenarJogos(jogos) {

    return [...jogos].sort(
        (a, b) => {

            const dataA =
                converterData(a.data);

            const dataB =
                converterData(b.data);

            if (!dataA && !dataB) {
                return 0;
            }

            if (!dataA) {
                return 1;
            }

            if (!dataB) {
                return -1;
            }

            return (
                dataB.getTime() -
                dataA.getTime()
            );
        }
    );
}


/* =========================
   FILTROS
========================= */

function configurarEventos() {

    elementos.busca.addEventListener(
        "input",
        aplicarFiltros
    );

    elementos.filtroTime.addEventListener(
        "change",
        aplicarFiltros
    );
}


function preencherFiltroTimes() {

    const times =
        [
            ...new Set(
                jogadores
                    .map(
                        jogador =>
                            jogador.time
                    )
                    .filter(Boolean)
            )
        ].sort(
            (a, b) =>
                a.localeCompare(
                    b,
                    "pt-BR"
                )
        );

    elementos.filtroTime.innerHTML =
        '<option value="">Todos os times</option>';

    times.forEach(time => {

        const opcao =
            document.createElement(
                "option"
            );

        opcao.value = time;
        opcao.textContent = time;

        elementos.filtroTime
            .appendChild(opcao);
    });
}


function aplicarFiltros() {

    const busca =
        normalizarTexto(
            elementos.busca.value
        );

    const time =
        elementos.filtroTime.value;

    const filtrados =
        jogadores.filter(
            jogador => {

                const correspondeNome =
                    normalizarTexto(
                        jogador.nome
                    ).includes(busca);

                const correspondeTime =
                    !time ||
                    jogador.time === time;

                return (
                    correspondeNome &&
                    correspondeTime
                );
            }
        );

    renderizarJogadores(
        filtrados
    );
}


/* =========================
   RENDERIZAÇÃO
========================= */

function renderizarJogadores(lista) {

    elementos.lista.innerHTML = "";

    elementos.total.textContent =
        lista.length;

    if (lista.length === 0) {

        elementos.semResultados.hidden =
            false;

        atualizarStatus(
            "Nenhum jogador encontrado."
        );

        return;
    }

    elementos.semResultados.hidden =
        true;

    lista.forEach(jogador => {

        elementos.lista.appendChild(
            criarCardJogador(
                jogador
            )
        );
    });

    atualizarStatus(
        `${lista.length} jogador(es) exibido(s).`
    );
}


/* =========================
   CARD
========================= */

function criarCardJogador(jogador) {

    const fragmento =
        elementos.template.content
            .cloneNode(true);

    definirTexto(
        fragmento,
        ".jogador-nome",
        jogador.nome
    );

    definirTexto(
        fragmento,
        ".jogador-time",
        jogador.time || "-"
    );

    definirTexto(
        fragmento,
        ".jogador-jogos",
        `${jogador.jogos.length} jogos recentes`
    );

    const medias =
        calcularMedias(
            jogador.jogos
        );

    definirTexto(
        fragmento,
        ".media-pts",
        medias.pts
    );

    definirTexto(
        fragmento,
        ".media-reb",
        medias.reb
    );

    definirTexto(
        fragmento,
        ".media-ast",
        medias.ast
    );

    definirTexto(
        fragmento,
        ".media-tpm",
        medias.tpm
    );

    definirTexto(
        fragmento,
        ".media-stl",
        medias.stl
    );

    definirTexto(
        fragmento,
        ".media-blk",
        medias.blk
    );

    const corpo =
        fragmento.querySelector(
            ".jogos-corpo"
        );

    jogador.jogos.forEach(
        jogo => {

            corpo.appendChild(
                criarLinhaJogo(
                    jogo
                )
            );
        }
    );

    return fragmento;
}


function definirTexto(
    fragmento,
    seletor,
    valor
) {

    const elemento =
        fragmento.querySelector(
            seletor
        );

    if (elemento) {
        elemento.textContent =
            valor;
    }
}


/* =========================
   JOGOS
========================= */

function criarLinhaJogo(jogo) {

    const linha =
        document.createElement(
            "tr"
        );

    const valores = [
        formatarData(jogo.data),
        jogo.adversario || "-",
        formatarNumero(jogo.pts),
        formatarNumero(jogo.reb),
        formatarNumero(jogo.ast),
        formatarNumero(jogo.tpm),
        formatarNumero(jogo.stl),
        formatarNumero(jogo.blk)
    ];

    valores.forEach(valor => {

        const celula =
            document.createElement(
                "td"
            );

        celula.textContent =
            valor;

        linha.appendChild(
            celula
        );
    });

    return linha;
}


/* =========================
   MÉDIAS
========================= */

function calcularMedias(jogos) {

    return {
        pts:
            calcularMedia(
                jogos,
                "pts"
            ),

        reb:
            calcularMedia(
                jogos,
                "reb"
            ),

        ast:
            calcularMedia(
                jogos,
                "ast"
            ),

        tpm:
            calcularMedia(
                jogos,
                "tpm"
            ),

        stl:
            calcularMedia(
                jogos,
                "stl"
            ),

        blk:
            calcularMedia(
                jogos,
                "blk"
            )
    };
}


function calcularMedia(
    jogos,
    campo
) {

    const valores =
        jogos
            .map(
                jogo =>
                    jogo[campo]
            )
            .filter(
                valor =>
                    typeof valor === "number" &&
                    Number.isFinite(valor)
            );

    if (valores.length === 0) {
        return "-";
    }

    const soma =
        valores.reduce(
            (total, valor) =>
                total + valor,
            0
        );

    return (
        soma /
        valores.length
    )
        .toFixed(1)
        .replace(".", ",");
}


/* =========================
   FORMATAÇÃO
========================= */

function formatarData(valor) {

    const data =
        converterData(valor);

    if (!data) {
        return valor || "-";
    }

    return data.toLocaleDateString(
        "pt-BR"
    );
}


function formatarNumero(valor) {

    if (
        valor === null ||
        valor === undefined ||
        !Number.isFinite(valor)
    ) {
        return "-";
    }

    return valor.toLocaleString(
        "pt-BR"
    );
}


function normalizarTexto(valor) {

    return String(valor || "")
        .normalize("NFD")
        .replace(
            /[\u0300-\u036f]/g,
            ""
        )
        .toLowerCase()
        .trim();
}


function atualizarStatus(texto) {

    elementos.status.textContent =
        texto;
}
