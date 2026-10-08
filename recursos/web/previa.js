// Previa da area de trabalho e da tela de login, desenhada com as opcoes
// marcadas na pagina (antes de aplicar), e a galeria de miniaturas das opcoes
// que escolhem uma imagem. As cores repetem as do projeto.py.
"use strict";

const Previa = (() => {
  const DESTAQUE = {areia: "#d9a45b", terracota: "#d9774f", oasis: "#2bb3a3", orchis: "#1a73e8"};
  const MODO = {
    escuro: {barra: "rgba(20,18,15,.62)", ilha: "rgba(28,23,20,.72)", texto: "#f2ece4",
             janela: "#2a2622", titulo: "#221e1b", lado: "#25211d", linha: "rgba(255,255,255,.10)"},
    claro:  {barra: "rgba(250,247,242,.70)", ilha: "rgba(250,245,237,.74)", texto: "#2a2420",
             janela: "#fbf9f6", titulo: "#efebe5", lado: "#f3efe9", linha: "rgba(0,0,0,.08)"},
  };
  const CORES_DOCK = ["#e8b04a", "#4a90d9", "#e2583e", "#5fb878", "#9b6cd6", "#d4d4d4"];
  // opcoes que viram galeria de miniaturas, no lugar de botoes ou lista
  const GALERIAS = ["cor_papel", "login_fundo"];

  let maximizada = false;
  // muda a cada imagem enviada, para o navegador nao usar a miniatura antiga
  let versaoPropria = 0;
  const el = (tag, classe, texto) => {
    const e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  };
  const hora = () => new Date().toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"});

  // a imagem de fundo de cada escolha; as da pessoa vem em miniatura pela API
  function papelDe(e){
    if (e.papel === "manter") return "/api/papel-atual.jpg";
    return `/exemplos/login_fundo-${e.cor_papel || "deserto"}-${e.papel === "degrade" ? "degrade" : "dunas"}.jpg`;
  }
  function fundoLoginDe(e){
    const v = e.login_fundo || "papel";
    if (v === "propria") return `/api/login-propria.jpg?v=${versaoPropria}`;
    if (v === "papel") return papelDe(e);
    return `/exemplos/login_fundo-${v}.jpg`;
  }
  function logoDe(e){
    const l = e.logo || "oasis";
    if (l === "oasis") return "/exemplos/logos/d3bian-oasis-logo.svg";
    if (l.endsWith("-cor")) return `/exemplos/logos/${l}.svg`;
    return `/exemplos/logos/${l}-${e.modo === "claro" ? "escuro" : "claro"}.svg`;
  }
  // imagem que pode nao existir (nenhuma escolhida, papel fora do xfdesktop):
  // o fundo listrado com o texto fica no lugar
  const faltam = new Set();
  function pintarFundo(caixa, url, texto){
    const sem = () => {
      caixa.style.backgroundImage = "";
      caixa.classList.add("sem-imagem");
      caixa.dataset.texto = texto;
    };
    if (!url || faltam.has(url)) return sem();
    caixa.classList.remove("sem-imagem");
    caixa.style.backgroundImage = `url("${url}")`;
    if (url.startsWith("/api/")){
      const prova = new Image();
      prova.onerror = () => { faltam.add(url); sem(); };
      prova.src = url;
    }
  }

  // ---- area de trabalho ---------------------------------------------------
  function desktop(e){
    const m = MODO[e.modo] || MODO.escuro;
    const acento = DESTAQUE[e.destaque] || DESTAQUE.areia;
    const tela = el("div", "pv-tela");
    tela.style.setProperty("--pv-acento", acento);
    tela.style.setProperty("--pv-texto", m.texto);
    pintarFundo(tela, papelDe(e), "papel de parede atual");

    const esconder = maximizada && e.paineis_maximizada !== "manter";
    const logo = el("img", "pv-logo"); logo.src = logoDe(e); logo.alt = "";
    const relogio = el("span", "pv-hora", hora());
    const dock = () => {
      const d = el("div", "pv-dock");
      CORES_DOCK.forEach(c => { const i = el("i"); i.style.background = c; d.appendChild(i); });
      return d;
    };

    if (e.paineis === "barra_unica"){
      const barra = el("div", "pv-barra-unica " + (e.barra_lado === "topo" ? "topo" : "baixo"));
      barra.style.background = m.barra;
      barra.append(logo, dock(), relogio);
      if (!esconder) tela.appendChild(barra);
    } else {
      const topo = el("div", "pv-topo");
      topo.style.background = m.barra;
      const icones = el("span", "pv-bandeja", "◦ ◦ ◦");
      topo.append(logo, el("span", "pv-esp"), icones, relogio);
      const ilhas = el("div", "pv-ilhas");
      const esq = el("div", "pv-ilha");
      const grade = el("span", "pv-grade");
      for (let i = 0; i < 4; i++) grade.appendChild(el("i"));
      esq.appendChild(grade);
      if (e.clima !== "nao") esq.appendChild(el("span", "pv-clima", "☀ 27°"));
      const meio = el("div", "pv-ilha"); meio.appendChild(dock());
      const dir = el("div", "pv-ilha pv-relogio");
      dir.append(el("b", "", hora()), el("span", "", "8 out"));
      [esq, meio, dir].forEach(i => { i.style.background = m.ilha; ilhas.appendChild(i); });
      if (!esconder) tela.append(topo, ilhas);
    }

    // uma janela de arquivos, com a selecao e o botao na cor de destaque
    const jan = el("div", "pv-janela" + (maximizada ? " cheia" : ""));
    jan.style.background = m.janela;
    jan.style.color = m.texto;
    const tit = el("div", "pv-tit");
    tit.style.background = m.titulo;
    tit.append(el("span", "", "Arquivos"), el("span", "pv-botoes", "–  ▢  ✕"));
    const corpo = el("div", "pv-corpo");
    const lado = el("div", "pv-lado");
    lado.style.background = m.lado;
    ["Pasta pessoal", "Documentos", "Imagens", "Downloads"].forEach((n, i) => {
      const item = el("div", "pv-item" + (i === 2 ? " sel" : ""), n);
      lado.appendChild(item);
    });
    const area = el("div", "pv-area");
    for (let i = 0; i < 4; i++){
      const l = el("i"); l.style.background = m.linha; l.style.width = (90 - i * 14) + "%"; area.appendChild(l);
    }
    area.appendChild(el("span", "pv-bt", "Abrir"));
    corpo.append(lado, area);
    jan.append(tit, corpo);
    tela.appendChild(jan);
    return tela;
  }

  // ---- tela de login ------------------------------------------------------
  function login(e){
    const acento = DESTAQUE[e.destaque] || DESTAQUE.areia;
    const tela = el("div", "pv-tela pv-login");
    tela.style.setProperty("--pv-acento", acento);
    const fundo = el("div", "pv-login-fundo" + (e.login_desfoque !== "nao" ? " desfocado" : ""));
    pintarFundo(fundo, fundoLoginDe(e), e.login_fundo === "propria"
      ? "escolha uma imagem nos ajustes" : "papel de parede atual");
    const topo = el("div", "pv-login-topo", `qui 8 out  ${hora()}  ⏻`);
    const meio = el("div", "pv-login-meio");
    const foto = el("div", "pv-foto");
    meio.appendChild(foto);
    if (e.login_usuarios === "lista") meio.appendChild(el("div", "pv-nome", "seu usuário ▾"));
    else meio.appendChild(el("div", "pv-campo", "Nome"));
    meio.appendChild(el("div", "pv-campo", "Senha"));
    const bts = el("div", "pv-login-bts");
    bts.append(el("span", "pv-bt-vidro", "Cancelar"), el("span", "pv-bt-entrar", "Entrar"));
    meio.appendChild(bts);
    tela.append(fundo, topo, meio);
    if (e.login === "nao") tela.appendChild(el("div", "pv-desligada", "Tela de login do sistema (sem a do oasis)"));
    return tela;
  }

  // ---- montagem -----------------------------------------------------------
  function desenhar(e){
    const caixa = document.querySelector("#previas");
    if (!caixa) return;
    caixa.textContent = "";
    caixa.hidden = false;

    const c1 = el("div", "cartao pv-cartao");
    c1.appendChild(el("h2", "", "Área de trabalho"));
    c1.appendChild(desktop(e));
    const pe = el("div", "pv-pe");
    pe.appendChild(el("span", "", "Muda na hora a cada opção; o desenho é aproximado."));
    if (e.paineis_maximizada !== "manter"){
      const b = el("button", "bt sec pv-alterna", maximizada ? "Ver janela normal" : "Ver janela maximizada");
      b.addEventListener("click", () => { maximizada = !maximizada; desenhar(e); });
      pe.appendChild(b);
    }
    c1.appendChild(pe);

    const c2 = el("div", "cartao pv-cartao");
    c2.appendChild(el("h2", "", "Tela de login e de bloqueio"));
    c2.appendChild(login(e));
    c2.appendChild(el("div", "pv-pe", "A de verdade aparece no próximo reinício; a de bloqueio muda na hora."));
    caixa.append(c1, c2);
  }

  // galeria de miniaturas: cada valor com a sua imagem, ou um texto
  function galeria(o, e, escolher){
    if (!GALERIAS.includes(o.chave)) return null;
    const g = el("div", "pv-galeria");
    o.valores.forEach(v => {
      const b = el("button", "pv-mini");
      b.type = "button";
      b.setAttribute("aria-pressed", String(e[o.chave] === v));
      const img = el("span", "pv-mini-img");
      let url = (o.exemplos || {})[v] ? `/exemplos/${o.exemplos[v]}` : null;
      if (o.chave === "login_fundo" && v === "papel") url = papelDe(e);
      pintarFundo(img, url, v === "propria" ? "nenhuma ainda" : "papel atual");
      if (v === "propria") url = `/api/login-propria.jpg?v=${versaoPropria}`;
      const nome = (o.nomes || {})[v] || v;
      b.append(img, el("span", "pv-mini-nome", nome));
      b.title = nome;
      b.addEventListener("click", () => escolher(v));
      g.appendChild(b);
    });
    if (o.chave !== "login_fundo") return g;

    // escolher uma imagem do computador: reduzida aqui, guardada pelo painel
    const caixa = el("div", "pv-galeria-caixa");
    const acoes = el("div", "pv-escolher");
    const entrada = el("input");
    entrada.type = "file";
    entrada.accept = "image/jpeg,image/png,image/webp";
    entrada.hidden = true;
    const botao = el("button", "bt sec", "Escolher imagem…");
    botao.type = "button";
    const aviso = el("span", "pv-aviso", "JPEG, PNG ou WebP; vai para o fundo do login");
    botao.addEventListener("click", () => entrada.click());
    entrada.addEventListener("change", async () => {
      const arquivo = entrada.files && entrada.files[0];
      entrada.value = "";
      if (!arquivo) return;
      botao.disabled = true;
      aviso.classList.remove("erro");
      aviso.textContent = "Preparando a imagem…";
      try {
        const imagem = await reduzir(arquivo);
        aviso.textContent = "Enviando…";
        const r = await fetch("/api/login-imagem", {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({imagem}),
        }).then(x => x.json());
        if (!r.ok) throw new Error(r.erro || "o painel recusou a imagem");
        versaoPropria++;
        faltam.forEach(u => { if (u.startsWith("/api/login-propria")) faltam.delete(u); });
        escolher("propria");
      } catch (erro){
        aviso.textContent = "Não deu: " + erro.message;
        aviso.classList.add("erro");
        botao.disabled = false;
      }
    });
    acoes.append(botao, aviso, entrada);
    caixa.append(g, acoes);
    return caixa;
  }

  // a foto inteira de uma camera passaria do limite do painel: sai em JPEG de
  // no maximo 2560x1600, que e mais do que a tela de login precisa
  function reduzir(arquivo){
    return new Promise((ok, falha) => {
      const url = URL.createObjectURL(arquivo);
      const img = new Image();
      img.onload = () => {
        const escala = Math.min(1, 2560 / img.naturalWidth, 1600 / img.naturalHeight);
        const c = document.createElement("canvas");
        c.width = Math.round(img.naturalWidth * escala);
        c.height = Math.round(img.naturalHeight * escala);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        ok(c.toDataURL("image/jpeg", 0.9).split(",")[1]);
      };
      img.onerror = () => { URL.revokeObjectURL(url); falha(new Error("o navegador não abriu essa imagem")); };
      img.src = url;
    });
  }

  return {desenhar, galeria};
})();
