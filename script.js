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

async function carregarDados() {
    atualizarStatus("Carregando jogadores...");

    try {
        const resposta = await fetch("./dados.csv", {
            cache: "no-store"
        });

        if (!resposta.ok) {
            throw new Error(`Erro ao carregar dados.csv: ${resposta.status}`);
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
        console.error(erro);

        jogadores = [];
        elementos.lista.innerHTML = "";
        elementos.total.textContent = "0";

        atualizarStatus(
            "Não foi possível carregar os dados dos jogadores."
        );
    }
}


/* LEITURA DO CSV */

function parseCSV(texto) {
    const linhas = [];
    let linha = [];
    let campo = "";
    let dentroAspas = false;

    for (let i = 0; i < texto.length; i++) {
        const caractere = texto[i];

        if (caractere === '"') {
            if (dentroAspas && texto[i + 1] === '"') {
                campo += '"';
                i++;
            } else {
                dentroAspas = !dentroAspas;
            }

        } else if (caractere === "," && !dentroAspas) {
            linha.push(campo);
            campo = "";

        } else if (
            (caractere === "\n" || caractere === "\r") &&
            !dentroAspas
        ) {
            if (
                caractere === "\r" &&
                texto[i + 1] === "\n"
            ) {
                i++;
            }

            linha.push(campo);

            if (linha.some(valor => valor.trim() !== "")) {
                linhas.push(linha);
            }

            linha = [];
            campo = "";

        } else {
            campo += caractere;
        }
    }

    if (campo.length > 0 || linha.length > 0) {
        linha.push(campo);

        if (linha.some(valor => valor.trim() !== "")) {
            linhas.push(linha);
        }
    }

    return linhas;
}


/* AGRUPAR JOGOS POR JOGADOR */

function agruparJogadores(linhas) {
    const cabecalhos = linhas[0].map(c =>
        c.replace(/^\uFEFF/, "").trim().toLowerCase()
    );

    const indice = {};

    cabecalhos.forEach((nome, i) => {
        indice[nome] = i;
    });

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
            adversario: valorCSV(colunas, indice.adversario),
            casa_fora: valorCSV(colunas, indice.casa_fora),
            minutos: numeroCSV(colunas, indice.minutos),
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
            jogos: jogador.jogos.slice(0, 10)
        }))
        .sort((a, b) =>
            a.nome.localeCompare(b.nome, "pt-BR")
        );
}

function valorCSV(colunas, posicao) {
    if (posicao === undefined) {
        return "";
    }

    return String(colunas[posicao] ?? "").trim();
}

function numeroCSV(colunas, posicao) {
    const valor = valorCSV(colunas, posicao);

    if (valor === "") {
        return null;
    }

    const numero = Number(
        valor.replace(",", ".")
    );

    return Number.isFinite(numero)
        ? numero
        : null;
}


/* FILTROS */

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
    const busca = normalizarTexto(
        elementos.busca.value
    );

    const time =
        elementos.filtroTime.value;

    const filtrados = jogadores.filter(jogador => {
        const correspondeNome =
            normalizarTexto(jogador.nome)
                .includes(busca);

        const correspondeTime =
            !time || jogador.time === time;

        return correspondeNome && correspondeTime;
    });

    renderizarJogadores(filtrados);
}

function preencherFiltroTimes() {
    const times = [
        ...new Set(
            jogadores
                .map(j => j.time)
                .filter(Boolean)
        )
    ].sort();

    elementos.filtroTime.innerHTML =
        '<option value="">Todos os times</option>';

    times.forEach(time => {
        const opcao =
            document.createElement("option");

        opcao.value = time;
        opcao.textContent = time;

        elementos.filtroTime
            .appendChild(opcao);
    });
}


/* CARDS */

function renderizarJogadores(lista) {
    elementos.lista.innerHTML = "";

    elementos.total.textContent =
        lista.length;

    if (!lista.length) {
        elementos.semResultados.hidden = false;

        atualizarStatus(
            "Nenhum jogador encontrado."
        );

        return;
    }

    elementos.semResultados.hidden = true;

    lista.forEach(jogador => {
        elementos.lista.appendChild(
            criarCardJogador(jogador)
        );
    });

    atualizarStatus(
        `${lista.length} jogador(es) exibido(s).`
    );
}

function criarCardJogador(jogador) {
    const fragmento =
        elementos.template.content.cloneNode(true);

    fragmento
        .querySelector(".jogador-nome")
        .textContent = jogador.nome;

    fragmento
        .querySelector(".jogador-time")
        .textContent = jogador.time;

    fragmento
        .querySelector(".jogador-jogos")
        .textContent =
            `${jogador.jogos.length} jogos recentes`;

    const medias =
        calcularMedias(jogador.jogos);

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
        ".media-stl",
        medias.stl
    );

    definirTexto(
        fragmento,
        ".media-blk",
        medias.blk
    );

    const corpo =
        fragmento.querySelector(".jogos-corpo");

    jogador.jogos.forEach(jogo => {
        corpo.appendChild(
            criarLinhaJogo(jogo)
        );
    });

    return fragmento;
}

function definirTexto(fragmento, seletor, valor) {
    const elemento =
        fragmento.querySelector(seletor);

    if (elemento) {
        elemento.textContent = valor;
    }
}


/* JOGOS */

function criarLinhaJogo(jogo) {
    const linha =
        document.createElement("tr");

    const valores = [
        formatarData(jogo.data),
        jogo.adversario || "-",
        formatarNumero(jogo.pts),
        formatarNumero(jogo.reb),
        formatarNumero(jogo.ast),
        formatarNumero(jogo.stl),
        formatarNumero(jogo.blk)
    ];

    valores.forEach(valor => {
        const celula =
            document.createElement("td");

        celula.textContent = valor;

        linha.appendChild(celula);
    });

    return linha;
}


/* MÉDIAS */

function calcularMedias(jogos) {
    return {
        pts: calcularMedia(jogos, "pts"),
        reb: calcularMedia(jogos, "reb"),
        ast: calcularMedia(jogos, "ast"),
        tpm: calcularMedia(jogos, "tpm"),
        stl: calcularMedia(jogos, "stl"),
        blk: calcularMedia(jogos, "blk")
    };
}

function calcularMedia(jogos, campo) {
    const valores = jogos
        .map(jogo => jogo[campo])
        .filter(valor =>
            typeof valor === "number"
            && Number.isFinite(valor)
        );

    if (!valores.length) {
        return "-";
    }

    const soma =
        valores.reduce(
            (total, valor) =>
                total + valor,
            0
        );

    return (soma / valores.length)
        .toFixed(1)
        .replace(".", ",");
}


/* FORMATAÇÃO */

function formatarNumero(valor) {
    if (
        valor === null ||
        valor === undefined
    ) {
        return "-";
    }

    return valor.toLocaleString("pt-BR");
}

function formatarData(valor) {
    if (!valor) {
        return "-";
    }

    const data =
        new Date(valor);

    if (Number.isNaN(data.getTime())) {
        return valor;
    }

    return data.toLocaleDateString(
        "pt-BR"
    );
}

function normalizarTexto(valor) {
    return String(valor || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}

function atualizarStatus(texto) {
    elementos.status.textContent = texto;
}
