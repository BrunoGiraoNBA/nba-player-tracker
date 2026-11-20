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


/* INICIALIZAÇÃO */

document.addEventListener("DOMContentLoaded", iniciar);

async function iniciar() {
    configurarEventos();
    await carregarDados();
}


/* CARREGAMENTO DOS DADOS */

async function carregarDados() {
    atualizarStatus("Carregando jogadores...");

    try {
        const resposta = await fetch("./dados.json", {
            cache: "no-store"
        });

        if (!resposta.ok) {
            throw new Error(
                `Não foi possível abrir dados.json. Erro ${resposta.status}.`
            );
        }

        const dados = await resposta.json();

        if (!Array.isArray(dados)) {
            throw new Error(
                "O conteúdo de dados.json precisa ser uma lista de jogadores."
            );
        }

        jogadores = normalizarJogadores(dados);

        preencherFiltroTimes();
        aplicarFiltros();

    } catch (erro) {
        console.error(erro);

        jogadores = [];
        elementos.lista.innerHTML = "";
        elementos.total.textContent = "0";
        elementos.semResultados.hidden = true;

        atualizarStatus(
            "Os dados ainda não foram adicionados. Falta criar o arquivo dados.json."
        );
    }
}


/* NORMALIZAÇÃO */

function normalizarJogadores(dados) {
    return dados.map((jogador) => {
        const jogos = Array.isArray(jogador.jogos)
            ? jogador.jogos.slice(0, 10)
            : [];

        return {
            nome: String(jogador.nome || "Jogador sem nome"),
            time: String(jogador.time || "SEM"),
            jogos
        };
    });
}


/* EVENTOS */

function configurarEventos() {
    elementos.busca.addEventListener("input", aplicarFiltros);
    elementos.filtroTime.addEventListener("change", aplicarFiltros);
}


/* FILTROS */

function aplicarFiltros() {
    const textoBusca = normalizarTexto(elementos.busca.value);
    const timeSelecionado = elementos.filtroTime.value;

    const jogadoresFiltrados = jogadores.filter((jogador) => {
        const correspondeNome =
            normalizarTexto(jogador.nome).includes(textoBusca);

        const correspondeTime =
            !timeSelecionado || jogador.time === timeSelecionado;

        return correspondeNome && correspondeTime;
    });

    renderizarJogadores(jogadoresFiltrados);
}


function preencherFiltroTimes() {
    const times = [...new Set(
        jogadores
            .map((jogador) => jogador.time)
            .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b, "pt-BR"));

    elementos.filtroTime.innerHTML =
        '<option value="">Todos os times</option>';

    times.forEach((time) => {
        const opcao = document.createElement("option");
        opcao.value = time;
        opcao.textContent = time;

        elementos.filtroTime.appendChild(opcao);
    });
}


/* RENDERIZAÇÃO */

function renderizarJogadores(listaJogadores) {
    elementos.lista.innerHTML = "";
    elementos.total.textContent = listaJogadores.length;

    if (listaJogadores.length === 0) {
        elementos.semResultados.hidden = false;

        atualizarStatus(
            jogadores.length === 0
                ? "Nenhum dado disponível."
                : "Nenhum jogador corresponde aos filtros."
        );

        return;
    }

    elementos.semResultados.hidden = true;

    listaJogadores.forEach((jogador) => {
        const card = criarCardJogador(jogador);
        elementos.lista.appendChild(card);
    });

    atualizarStatus(
        `${listaJogadores.length} jogador(es) exibido(s).`
    );
}


function criarCardJogador(jogador) {
    const fragmento =
        elementos.template.content.cloneNode(true);

    fragmento.querySelector(".jogador-nome").textContent =
        jogador.nome;

    fragmento.querySelector(".jogador-time").textContent =
        jogador.time;

    const quantidadeJogos = jogador.jogos.length;

    fragmento.querySelector(".jogador-jogos").textContent =
        quantidadeJogos === 1
            ? "1 jogo recente"
            : `${quantidadeJogos} jogos recentes`;

    const medias = calcularMedias(jogador.jogos);

    fragmento.querySelector(".media-pts").textContent = medias.pts;
    fragmento.querySelector(".media-reb").textContent = medias.reb;
    fragmento.querySelector(".media-ast").textContent = medias.ast;
    fragmento.querySelector(".media-stl").textContent = medias.stl;
    fragmento.querySelector(".media-blk").textContent = medias.blk;

    const corpoTabela =
        fragmento.querySelector(".jogos-corpo");

    if (jogador.jogos.length === 0) {
        corpoTabela.appendChild(criarLinhaSemJogos());
    } else {
        jogador.jogos.forEach((jogo) => {
            corpoTabela.appendChild(criarLinhaJogo(jogo));
        });
    }

    return fragmento;
}


function criarLinhaJogo(jogo) {
    const linha = document.createElement("tr");

    const valores = [
        formatarData(jogo.data),
        jogo.adversario || "-",
        formatarNumero(jogo.pts),
        formatarNumero(jogo.reb),
        formatarNumero(jogo.ast),
        formatarNumero(jogo.stl),
        formatarNumero(jogo.blk)
    ];

    valores.forEach((valor) => {
        const celula = document.createElement("td");
        celula.textContent = valor;
        linha.appendChild(celula);
    });

    return linha;
}


function criarLinhaSemJogos() {
    const linha = document.createElement("tr");
    const celula = document.createElement("td");

    celula.colSpan = 7;
    celula.textContent = "Nenhum jogo disponível.";
    celula.style.textAlign = "center";

    linha.appendChild(celula);

    return linha;
}


/* CÁLCULO DAS MÉDIAS */

function calcularMedias(jogos) {
    if (!jogos.length) {
        return {
            pts: "-",
            reb: "-",
            ast: "-",
            stl: "-",
            blk: "-"
        };
    }

    return {
        pts: calcularMedia(jogos, "pts"),
        reb: calcularMedia(jogos, "reb"),
        ast: calcularMedia(jogos, "ast"),
        stl: calcularMedia(jogos, "stl"),
        blk: calcularMedia(jogos, "blk")
    };
}


function calcularMedia(jogos, campo) {
    const valores = jogos
        .map((jogo) => Number(jogo[campo]))
        .filter((valor) => Number.isFinite(valor));

    if (!valores.length) {
        return "-";
    }

    const total = valores.reduce(
        (soma, valor) => soma + valor,
        0
    );

    return (total / valores.length)
        .toFixed(1)
        .replace(".", ",");
}


/* FORMATAÇÃO */

function formatarData(valor) {
    if (!valor) {
        return "-";
    }

    const texto = String(valor);

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(texto)) {
        return texto;
    }

    const data = new Date(texto);

    if (Number.isNaN(data.getTime())) {
        return texto;
    }

    return data.toLocaleDateString("pt-BR");
}


function formatarNumero(valor) {
    if (
        valor === null ||
        valor === undefined ||
        valor === ""
    ) {
        return "-";
    }

    const numero = Number(valor);

    return Number.isFinite(numero)
        ? numero.toLocaleString("pt-BR")
        : String(valor);
}


function normalizarTexto(valor) {
    return String(valor || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}


function atualizarStatus(mensagem) {
    elementos.status.textContent = mensagem;
}
