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


/* =========================
   INICIALIZAÇÃO
========================= */

document.addEventListener("DOMContentLoaded", iniciar);

async function iniciar() {
    configurarEventos();
    await carregarDados();
}


/* =========================
   CARREGAMENTO DO CSV
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

        const linhas = parseCSV(texto);

        if (linhas.length < 2) {
            throw new Error("dados.csv está vazio.");
        }

        jogadores = agruparJogadores(linhas);

        preencherFiltroTimes();
        aplicarFiltros();

    } catch (erro) {
        console.error("Erro ao carregar dados:", erro);

        jogadores = [];

        elementos.lista.innerHTML = "";
        elementos.total.textContent = "0";
        elementos.semResultados.hidden = true;

        atualizarStatus(
            "Não foi possível carregar os dados dos jogadores."
        );
    }
}


/* =========================
   LEITOR CSV
========================= */

function parseCSV(texto) {
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
            caractere === "," &&
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
   AGRUPAMENTO DOS JOGADORES
========================= */

function agruparJogadores(linhas) {

    const cabecalhos = linhas[0].map(
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

    const colunasObrigatorias = [
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
        colunasObrigatorias.filter(
            coluna =>
                indice[coluna] === undefined
        );

    if (faltando.length > 0) {
        throw new Error(
            "Colunas ausentes no CSV: " +
            faltando.join(", ")
        );
    }

    const mapa = new Map();

    linhas.slice(1).forEach(colunas => {

        const nome =
            valorCSV(colunas, indice.nome);

        if (!nome) {
            return;
        }

        const time =
            valorCSV(colunas, indice.time);

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

        const jogador =
            mapa.get(nome);

        jogador.jogos.push({
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

    return Array.from(
        mapa.values()
    )
        .map(jogador => ({
            ...jogador,

            jogos:
                ordenarJogosPorData(
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
   UTILIDADES CSV
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

    const tratado =
        valor
            .replace(/\s/g, "")
            .replace(",", ".");

    const numero =
        Number(tratado);

    return Number.isFinite(numero)
        ? numero
        : null;
}


/* =========================
   ORDENAÇÃO DOS JOGOS
========================= */

function ordenarJogosPorData(jogos) {

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
            jogadores.length === 0
                ? "Nenhum dado disponível."
                : "Nenhum jogador corresponde aos filtros."
        );

        return;
    }

    elementos.semResultados.hidden =
        true;

    lista.forEach(jogador => {

        const card =
            criarCardJogador(
                jogador
            );

        elementos.lista
            .appendChild(card);
    });

    atualizarStatus(
        `${lista.length} jogador(es) exibido(s).`
    );
}


/* =========================
   CARD DO JOGADOR
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
        jogador.jogos.length === 1
            ? "1 jogo recente"
            : `${jogador.jogos.length} jogos recentes`
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

    const corpoTabela =
        fragmento.querySelector(
            ".jogos-corpo"
        );

    if (jogador.jogos.length === 0) {

        corpoTabela.appendChild(
            criarLinhaSemJogos()
        );

    } else {

        jogador.jogos.forEach(
            jogo => {

                corpoTabela.appendChild(
                    criarLinhaJogo(
                        jogo
                    )
                );
            }
        );
    }

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
   LINHAS DE JOGO
========================= */

function criarLinhaJogo(jogo) {

    const linha =
        document.createElement("tr");

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


function criarLinhaSemJogos() {

    const linha =
        document.createElement("tr");

    const celula =
        document.createElement("td");

    celula.colSpan = 8;

    celula.textContent =
        "Nenhum jogo disponível.";

    celula.style.textAlign =
        "center";

    linha.appendChild(celula);

    return linha;
}


/* =========================
   MÉDIAS DOS ÚLTIMOS 10
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
                    typeof valor ===
                        "number" &&
                    Number.isFinite(
                        valor
                    )
            );

    if (valores.length === 0) {
        return "-";
    }

    const soma =
        valores.reduce(
            (
                total,
                valor
            ) =>
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
   DATAS
========================= */

function converterData(valor) {

    if (!valor) {
        return null;
    }

    const texto =
        String(valor).trim();

    /*
       Formato esperado do CSV:
       Nov 18, 2026
    */

    let data =
        new Date(texto);

    if (
        !Number.isNaN(
            data.getTime()
        )
    ) {
        return data;
    }

    /*
       Fallback:
       dd/mm/aaaa
    */

    const partes =
        texto.match(
            /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/
        );

    if (partes) {

        data =
            new Date(
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


/* =========================
   FORMATAÇÃO
========================= */

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
