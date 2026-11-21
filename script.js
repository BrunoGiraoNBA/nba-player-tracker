const elementos = {
    busca: document.getElementById("busca-jogador"),
    listaTimes: document.getElementById("lista-times"),
    limparTimes: document.getElementById("limpar-times"),

    seletorJogador: document.getElementById("seletor-jogador"),
    adicionarJogador: document.getElementById("adicionar-jogador"),
    jogadoresSelecionados: document.getElementById(
        "jogadores-selecionados"
    ),
    limparJogadores: document.getElementById("limpar-jogadores"),

    quantidadeSelecionados: document.getElementById(
        "quantidade-selecionados"
    ),

    mostrarTodos: document.getElementById("mostrar-todos"),
    mostrarSelecionados: document.getElementById(
        "mostrar-selecionados"
    ),
    limparTudo: document.getElementById("limpar-tudo"),

    lista: document.getElementById("lista-jogadores"),
    status: document.getElementById("status-texto"),
    total: document.getElementById("total-jogadores"),
    semResultados: document.getElementById("sem-resultados"),
    template: document.getElementById("template-jogador")
};

let jogadores = [];

const estado = {
    timesSelecionados: new Set(),
    jogadoresSelecionados: new Set(),
    modoExibicao: "filtrados"
};


document.addEventListener("DOMContentLoaded", iniciar);


/* ==================================================
   INICIALIZAÇÃO
================================================== */

async function iniciar() {
    configurarEventos();
    await carregarDados();
}


/* ==================================================
   CARREGAMENTO DO CSV
================================================== */

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

        criarOpcoesTimes();
        preencherSeletorJogadores();
        atualizarTodaInterface();

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


/* ==================================================
   DETECÇÃO DO SEPARADOR
================================================== */

function detectarSeparador(texto) {
    const primeiraLinha = texto.split(/\r?\n/)[0] || "";

    const quantidadePontoVirgula =
        (primeiraLinha.match(/;/g) || []).length;

    const quantidadeVirgula =
        (primeiraLinha.match(/,/g) || []).length;

    return quantidadePontoVirgula > quantidadeVirgula
        ? ";"
        : ",";
}


/* ==================================================
   LEITOR CSV
================================================== */

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


/* ==================================================
   AGRUPAMENTO DOS JOGADORES
================================================== */

function agruparJogadores(linhas) {
    const cabecalhos = linhas[0].map(
        cabecalho =>
            String(cabecalho)
                .replace(/^\uFEFF/, "")
                .trim()
                .toLowerCase()
    );

    const indice = {};

    cabecalhos.forEach((nome, posicao) => {
        indice[nome] = posicao;
    });

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

    const faltando = obrigatorias.filter(
        coluna => indice[coluna] === undefined
    );

    if (faltando.length > 0) {
        throw new Error(
            "Colunas ausentes: " + faltando.join(", ")
        );
    }

    const mapa = new Map();

    linhas.slice(1).forEach(colunas => {
        const nome = valorCSV(colunas, indice.nome);

        if (!nome) {
            return;
        }

        const time = valorCSV(colunas, indice.time);

        if (!mapa.has(nome)) {
            mapa.set(nome, {
                nome,
                time,
                jogos: []
            });
        }

        mapa.get(nome).jogos.push({
            data: valorCSV(colunas, indice.data),

            adversario: valorCSV(
                colunas,
                indice.adversario
            ),

            casa_fora: valorCSV(
                colunas,
                indice.casa_fora
            ),

            minutos: numeroCSV(
                colunas,
                indice.minutos
            ),

            pts: numeroCSV(colunas, indice.pts),
            reb: numeroCSV(colunas, indice.reb),
            ast: numeroCSV(colunas, indice.ast),
            tpm: numeroCSV(colunas, indice.tpm),
            stl: numeroCSV(colunas, indice.stl),
            blk: numeroCSV(colunas, indice.blk)
        });
    });

    return Array.from(mapa.values())
        .map(jogador => ({
            ...jogador,
            jogos: ordenarJogos(
                jogador.jogos
            ).slice(0, 10)
        }))
        .sort((a, b) =>
            a.nome.localeCompare(b.nome, "pt-BR")
        );
}


/* ==================================================
   VALORES CSV
================================================== */

function valorCSV(colunas, posicao) {
    if (posicao === undefined) {
        return "";
    }

    return String(
        colunas[posicao] ?? ""
    ).trim();
}


function numeroCSV(colunas, posicao) {
    const valor = valorCSV(colunas, posicao);

    if (valor === "") {
        return null;
    }

    const numero = Number(
        valor
            .replace(/\s/g, "")
            .replace(",", ".")
    );

    return Number.isFinite(numero)
        ? numero
        : null;
}


/* ==================================================
   DATAS E ORDENAÇÃO
================================================== */

function converterData(valor) {
    if (!valor) {
        return null;
    }

    const texto = String(valor).trim();

    let data = new Date(texto);

    if (!Number.isNaN(data.getTime())) {
        return data;
    }

    const partes = texto.match(
        /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/
    );

    if (partes) {
        data = new Date(
            Number(partes[3]),
            Number(partes[2]) - 1,
            Number(partes[1])
        );

        if (!Number.isNaN(data.getTime())) {
            return data;
        }
    }

    return null;
}


function ordenarJogos(jogos) {
    return [...jogos].sort((a, b) => {
        const dataA = converterData(a.data);
        const dataB = converterData(b.data);

        if (!dataA && !dataB) {
            return 0;
        }

        if (!dataA) {
            return 1;
        }

        if (!dataB) {
            return -1;
        }

        return dataB.getTime() - dataA.getTime();
    });
}


/* ==================================================
   EVENTOS
================================================== */

function configurarEventos() {
    elementos.busca.addEventListener(
        "input",
        atualizarTodaInterface
    );

    elementos.adicionarJogador.addEventListener(
        "click",
        adicionarJogadorSelecionado
    );

    elementos.seletorJogador.addEventListener(
        "change",
        atualizarBotaoAdicionar
    );

    elementos.seletorJogador.addEventListener(
        "keydown",
        evento => {
            if (evento.key === "Enter") {
                evento.preventDefault();
                adicionarJogadorSelecionado();
            }
        }
    );

    elementos.limparTimes.addEventListener(
        "click",
        limparSelecaoTimes
    );

    elementos.limparJogadores.addEventListener(
        "click",
        limparSelecaoJogadores
    );

    elementos.mostrarTodos.addEventListener(
        "click",
        () => alterarModoExibicao("filtrados")
    );

    elementos.mostrarSelecionados.addEventListener(
        "click",
        () => alterarModoExibicao("selecionados")
    );

    elementos.limparTudo.addEventListener(
        "click",
        limparTodosFiltros
    );
}


/* ==================================================
   TIMES
================================================== */

function criarOpcoesTimes() {
    const times = [
        ...new Set(
            jogadores
                .map(jogador => jogador.time)
                .filter(Boolean)
        )
    ].sort((a, b) =>
        a.localeCompare(b, "pt-BR")
    );

    elementos.listaTimes.innerHTML = "";

    times.forEach(time => {
        const item = document.createElement("div");
        item.className = "time-opcao";

        const input = document.createElement("input");
        input.type = "checkbox";
        input.id = `time-${criarIdentificador(time)}`;
        input.value = time;

        const label = document.createElement("label");
        label.htmlFor = input.id;
        label.textContent = time;

        input.addEventListener("change", () => {
            if (input.checked) {
                /*
                   Set mantém a ordem de inserção.

                   Portanto:
                   clicar DEN e depois LAL
                   gera a ordem:
                   DEN -> LAL
                */
                estado.timesSelecionados.add(time);

            } else {
                estado.timesSelecionados.delete(time);
            }

            atualizarTodaInterface();
        });

        item.appendChild(input);
        item.appendChild(label);

        elementos.listaTimes.appendChild(item);
    });
}


function limparSelecaoTimes() {
    estado.timesSelecionados.clear();

    elementos.listaTimes
        .querySelectorAll('input[type="checkbox"]')
        .forEach(input => {
            input.checked = false;
        });

    atualizarTodaInterface();
}


/* ==================================================
   SELETOR DE JOGADORES
================================================== */

function preencherSeletorJogadores() {
    const valorAtual = elementos.seletorJogador.value;

    elementos.seletorJogador.innerHTML = "";

    const opcaoInicial = document.createElement("option");
    opcaoInicial.value = "";
    opcaoInicial.textContent = "Selecione um jogador";

    elementos.seletorJogador.appendChild(opcaoInicial);

    jogadores.forEach(jogador => {
        const opcao = document.createElement("option");

        opcao.value = jogador.nome;
        opcao.textContent =
            `${jogador.nome} • ${jogador.time}`;

        opcao.disabled =
            estado.jogadoresSelecionados.has(
                jogador.nome
            );

        elementos.seletorJogador.appendChild(opcao);
    });

    if (
        valorAtual &&
        !estado.jogadoresSelecionados.has(valorAtual)
    ) {
        elementos.seletorJogador.value = valorAtual;
    }

    atualizarBotaoAdicionar();
}


function atualizarBotaoAdicionar() {
    const nome = elementos.seletorJogador.value;

    elementos.adicionarJogador.disabled =
        !nome ||
        estado.jogadoresSelecionados.has(nome);
}


function adicionarJogadorSelecionado() {
    const nome = elementos.seletorJogador.value;

    if (
        !nome ||
        estado.jogadoresSelecionados.has(nome)
    ) {
        return;
    }

    estado.jogadoresSelecionados.add(nome);

    elementos.seletorJogador.value = "";

    preencherSeletorJogadores();
    atualizarTodaInterface();
}


function removerJogadorSelecionado(nome) {
    estado.jogadoresSelecionados.delete(nome);

    preencherSeletorJogadores();
    atualizarTodaInterface();
}


function limparSelecaoJogadores() {
    estado.jogadoresSelecionados.clear();

    preencherSeletorJogadores();
    atualizarTodaInterface();
}


/* ==================================================
   CHIPS
================================================== */

function renderizarChipsSelecionados() {
    elementos.jogadoresSelecionados.innerHTML = "";

    const nomes = Array.from(
        estado.jogadoresSelecionados
    );

    nomes.forEach(nome => {
        const jogador = jogadores.find(
            item => item.nome === nome
        );

        const chip = document.createElement("div");
        chip.className = "jogador-chip";

        const texto = document.createElement("span");

        texto.textContent = jogador
            ? `${jogador.nome} • ${jogador.time}`
            : nome;

        const remover = document.createElement("button");

        remover.type = "button";
        remover.textContent = "×";
        remover.title = `Remover ${nome}`;

        remover.setAttribute(
            "aria-label",
            `Remover ${nome}`
        );

        remover.addEventListener("click", () => {
            removerJogadorSelecionado(nome);
        });

        chip.appendChild(texto);
        chip.appendChild(remover);

        elementos.jogadoresSelecionados.appendChild(
            chip
        );
    });

    elementos.quantidadeSelecionados.textContent =
        estado.jogadoresSelecionados.size;
}


/* ==================================================
   MODO DE EXIBIÇÃO
================================================== */

function alterarModoExibicao(modo) {
    estado.modoExibicao = modo;

    atualizarBotoesModo();
    atualizarTodaInterface();
}


function atualizarBotoesModo() {
    const mostrandoFiltrados =
        estado.modoExibicao === "filtrados";

    elementos.mostrarTodos.classList.toggle(
        "ativo",
        mostrandoFiltrados
    );

    elementos.mostrarSelecionados.classList.toggle(
        "ativo",
        !mostrandoFiltrados
    );
}


/* ==================================================
   LIMPAR TUDO
================================================== */

function limparTodosFiltros() {
    estado.timesSelecionados.clear();
    estado.jogadoresSelecionados.clear();
    estado.modoExibicao = "filtrados";

    elementos.busca.value = "";
    elementos.seletorJogador.value = "";

    elementos.listaTimes
        .querySelectorAll('input[type="checkbox"]')
        .forEach(input => {
            input.checked = false;
        });

    preencherSeletorJogadores();
    atualizarTodaInterface();
}


/* ==================================================
   ORDENAÇÃO POR TIME SELECIONADO

   Exemplo:
   1. DEN selecionado
   2. LAL selecionado

   Resultado:
   todos DEN em ordem alfabética
   depois todos LAL em ordem alfabética
================================================== */

function ordenarPorTimesSelecionados(lista) {
    if (estado.timesSelecionados.size === 0) {
        return [...lista].sort(
            (a, b) =>
                a.nome.localeCompare(
                    b.nome,
                    "pt-BR"
                )
        );
    }

    const ordemTimes =
        Array.from(
            estado.timesSelecionados
        );

    const posicaoTime =
        new Map();

    ordemTimes.forEach(
        (time, indice) => {
            posicaoTime.set(
                time,
                indice
            );
        }
    );

    return [...lista].sort(
        (a, b) => {
            const posicaoA =
                posicaoTime.has(a.time)
                    ? posicaoTime.get(a.time)
                    : Number.MAX_SAFE_INTEGER;

            const posicaoB =
                posicaoTime.has(b.time)
                    ? posicaoTime.get(b.time)
                    : Number.MAX_SAFE_INTEGER;

            if (posicaoA !== posicaoB) {
                return posicaoA - posicaoB;
            }

            return a.nome.localeCompare(
                b.nome,
                "pt-BR"
            );
        }
    );
}


/* ==================================================
   FILTRAGEM
================================================== */

function obterJogadoresExibidos() {
    const busca = normalizarTexto(
        elementos.busca.value
    );

    /*
       MODO SOMENTE SELECIONADOS
    */

    if (
        estado.modoExibicao ===
        "selecionados"
    ) {
        const selecionados =
            jogadores.filter(
                jogador => {
                    const foiSelecionado =
                        estado.jogadoresSelecionados.has(
                            jogador.nome
                        );

                    const correspondeBusca =
                        normalizarTexto(
                            jogador.nome
                        ).includes(busca);

                    return (
                        foiSelecionado &&
                        correspondeBusca
                    );
                }
            );

        /*
           Se houver times marcados,
           mantém os jogadores selecionados
           agrupados nessa mesma ordem.
        */

        return ordenarPorTimesSelecionados(
            selecionados
        );
    }


    /*
       MODO MOSTRAR FILTRADOS
    */

    const filtrados =
        jogadores.filter(
            jogador => {
                const correspondeBusca =
                    normalizarTexto(
                        jogador.nome
                    ).includes(busca);

                const correspondeTime =
                    estado.timesSelecionados.size === 0 ||
                    estado.timesSelecionados.has(
                        jogador.time
                    );

                return (
                    correspondeBusca &&
                    correspondeTime
                );
            }
        );

    return ordenarPorTimesSelecionados(
        filtrados
    );
}


/* ==================================================
   ATUALIZAÇÃO GERAL
================================================== */

function atualizarTodaInterface() {
    renderizarChipsSelecionados();
    atualizarBotoesModo();
    atualizarBotaoAdicionar();

    const lista = obterJogadoresExibidos();

    renderizarJogadores(lista);
}


/* ==================================================
   RENDERIZAÇÃO DOS JOGADORES
================================================== */

function renderizarJogadores(lista) {
    elementos.lista.innerHTML = "";
    elementos.total.textContent = lista.length;

    if (lista.length === 0) {
        elementos.semResultados.hidden = false;

        if (
            estado.modoExibicao === "selecionados" &&
            estado.jogadoresSelecionados.size === 0
        ) {
            atualizarStatus(
                "Nenhum jogador foi selecionado."
            );

        } else {
            atualizarStatus(
                "Nenhum jogador encontrado com os filtros selecionados."
            );
        }

        return;
    }

    elementos.semResultados.hidden = true;

    lista.forEach(jogador => {
        elementos.lista.appendChild(
            criarCardJogador(jogador)
        );
    });

    atualizarStatus(
        criarMensagemStatus(lista.length)
    );
}


function criarMensagemStatus(quantidade) {
    const partes = [];

    partes.push(
        `${quantidade} jogador(es) exibido(s)`
    );

    if (estado.timesSelecionados.size > 0) {
        partes.push(
            Array.from(
                estado.timesSelecionados
            ).join(" → ")
        );
    }

    if (
        estado.jogadoresSelecionados.size >
        0
    ) {
        partes.push(
            `${estado.jogadoresSelecionados.size} selecionado(s)`
        );
    }

    if (
        estado.modoExibicao ===
        "selecionados"
    ) {
        partes.push(
            "modo somente selecionados"
        );
    }

    return partes.join(" • ") + ".";
}


/* ==================================================
   CARD DO JOGADOR
================================================== */

function criarCardJogador(jogador) {
    const fragmento =
        elementos.template.content.cloneNode(true);

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

    const corpo =
        fragmento.querySelector(
            ".jogos-corpo"
        );

    if (
        jogador.jogos.length === 0
    ) {
        corpo.appendChild(
            criarLinhaSemJogos()
        );

    } else {
        jogador.jogos.forEach(
            jogo => {
                corpo.appendChild(
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


/* ==================================================
   LINHAS DOS JOGOS
================================================== */

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


function criarLinhaSemJogos() {
    const linha =
        document.createElement(
            "tr"
        );

    const celula =
        document.createElement(
            "td"
        );

    celula.colSpan = 8;
    celula.textContent =
        "Nenhum jogo disponível.";

    celula.style.textAlign =
        "center";

    linha.appendChild(
        celula
    );

    return linha;
}


/* ==================================================
   MÉDIAS
================================================== */

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

    if (
        valores.length === 0
    ) {
        return "-";
    }

    const soma =
        valores.reduce(
            (
                total,
                valor
            ) =>
                total +
                valor,
            0
        );

    return (
        soma /
        valores.length
    )
        .toFixed(1)
        .replace(".", ",");
}


/* ==================================================
   FORMATAÇÃO
================================================== */

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


function criarIdentificador(valor) {
    return normalizarTexto(valor)
        .replace(
            /[^a-z0-9]+/g,
            "-"
        )
        .replace(
            /^-+|-+$/g,
            ""
        );
}


function atualizarStatus(texto) {
    elementos.status.textContent =
        texto;
}
