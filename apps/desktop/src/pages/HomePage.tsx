import { openUrl } from "@tauri-apps/plugin-opener";
import clsx from "clsx";
import { lazy, Suspense, useEffect, useState } from "react";
import {
  Activity,
  AudioLines,
  BrainCircuit,
  Clock3,
  Database,
  ExternalLink,
  Globe2,
  HardDrive,
  MessageSquareText,
  Mic2,
  MonitorCog,
  Radio,
  Search,
  ShieldCheck,
  Wifi,
} from "lucide-react";
import { StatusDot } from "../components/StatusDot";
import { TamagotchiCompanion } from "../components/TamagotchiCompanion";
import { useKaironSocket } from "../hooks/useKaironSocket";
import { useKaironStore } from "../stores/kaironStore";
import type { KaironState } from "../types/kairon";

const KaironScene = lazy(() =>
  import("../components/KaironScene").then((module) => ({ default: module.KaironScene })),
);

const stateLabel: Record<KaironState, string> = {
  idle: "Inicializando",
  listening_for_wake_word: "Em espera",
  wake_word_detected: "Canal aberto",
  listening: "Ouvindo",
  processing: "Interpretando",
  thinking: "Processando",
  speaking: "Respondendo",
  executing: "Executando",
  error: "Falha no sistema",
  offline: "Reconectando",
};

const stateDetail: Record<KaironState, string> = {
  idle: "Sincronizando sistemas locais",
  listening_for_wake_word: "Escuta contínua ativa",
  wake_word_detected: "Comando de voz autorizado",
  listening: "Capturando sua voz",
  processing: "Analisando o comando",
  thinking: "Construindo a melhor resposta",
  speaking: "Transmitindo resposta por voz",
  executing: "Aplicando comando autorizado",
  error: "Verifique o registro de atividade",
  offline: "Procurando o nucleo local",
};

function messageLabel(role: "user" | "assistant" | "system") {
  if (role === "user") return "Voce";
  if (role === "assistant") return "Kairon";
  return "Sistema";
}

export function HomePage() {
  useKaironSocket();
  const [now, setNow] = useState(() => new Date());
  const { state, connected, microphoneActive, memoryCount, transcript, messages } =
    useKaironStore();
  const latestResponse = [...messages].reverse().find((message) => message.role === "assistant")?.text ?? "";
  const recentMessages = messages.slice(-3);
  const active = connected && state !== "error" && state !== "offline";
  const day = now.toLocaleDateString("pt-BR", { day: "2-digit" });
  const month = now
    .toLocaleDateString("pt-BR", { month: "short" })
    .replace(".", "")
    .toUpperCase();
  const weekday = now.toLocaleDateString("pt-BR", { weekday: "long" });
  const time = now.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <main className="command-shell" data-state={state} data-tauri-drag-region>
      <Suspense fallback={<div className="kairon-scene kairon-scene--loading" />}>
        <KaironScene state={state} />
      </Suspense>
      <div className="hud-frame" aria-hidden="true">
        <span className="hud-corner hud-corner--tl" />
        <span className="hud-corner hud-corner--tr" />
        <span className="hud-corner hud-corner--bl" />
        <span className="hud-corner hud-corner--br" />
        <span className="hud-scanline" />
      </div>

      <div className="command-layout">
        <header className="command-header">
          <div className="brand-lockup">
            <div className="brand-mark" aria-hidden="true"><BrainCircuit /></div>
            <div>
              <h1>Kairon</h1>
              <p>Interface cognitiva local</p>
            </div>
          </div>
          <div className="header-clock" aria-label={`Horario local ${time}`}>
            <Clock3 aria-hidden="true" />
            <time dateTime={now.toISOString()}>{time}</time>
            <span>LOCAL</span>
          </div>
          <div className="header-telemetry">
            <span className="header-code">KN // 01</span>
            <StatusDot active={active} label={active ? "Online" : "Offline"} />
            <ShieldCheck aria-hidden="true" />
          </div>
        </header>

        <aside className="telemetry-rail" aria-label="Sistemas principais">
          <div className="date-module">
            <div className="date-orbit" aria-hidden="true"><span /></div>
            <div className="date-content">
              <span>{month}</span>
              <strong>{day}</strong>
              <small>{weekday}</small>
            </div>
          </div>

          <div className="rail-heading"><Activity aria-hidden="true" /><span>Sistemas</span></div>
          <dl className="telemetry-list">
            <div>
              <dt><Wifi aria-hidden="true" /> Nucleo</dt>
              <dd>{connected ? "Conectado" : "Indisponivel"}</dd>
            </div>
            <div>
              <dt><Mic2 aria-hidden="true" /> Microfone</dt>
              <dd>{microphoneActive ? "Escuta ativa" : "Em espera"}</dd>
            </div>
            <div>
              <dt><Database aria-hidden="true" /> Memoria local</dt>
              <dd>{memoryCount.toString().padStart(2, "0")} fatos</dd>
            </div>
            <div>
              <dt><MessageSquareText aria-hidden="true" /> Historico</dt>
              <dd>{messages.length.toString().padStart(2, "0")} mensagens</dd>
            </div>
          </dl>
          <div className="signal-block" aria-label={microphoneActive ? "Sinal de voz ativo" : "Sinal de voz em espera"}>
            {Array.from({ length: 14 }, (_, index) => <span key={index} />)}
          </div>
          <p className="rail-coordinate">CORE 127.0.0.1 // ENCRYPTED</p>
        </aside>

        <section className="command-focus" aria-labelledby="voice-state">
          <div className="focus-index"><Radio aria-hidden="true" /> VOICE CORE // LIVE</div>
          <div
            className="state-readout"
            aria-live="polite"
            role={state === "error" ? "alert" : "status"}
          >
            <p className="state-sequence">STATUS // {state.replaceAll("_", " ")}</p>
            <h2 id="voice-state">{stateLabel[state]}</h2>
            <p>{stateDetail[state]}</p>
          </div>
          <TamagotchiCompanion state={state} transcript={transcript} response={latestResponse} />
          <div className={clsx("voice-wave", microphoneActive && "voice-wave--active")} aria-hidden="true">
            {Array.from({ length: 30 }, (_, index) => <span key={index} />)}
          </div>
          <div className={clsx("transcript-band", !transcript && "transcript-band--empty")}>
            <AudioLines aria-hidden="true" />
            <div>
              <span>Entrada reconhecida</span>
              <p>{transcript || "Aguardando sua voz"}</p>
            </div>
          </div>
        </section>

        <aside className="intelligence-rail" aria-label="Informacoes da Kairon">
          <section className="memory-module" aria-label={`${memoryCount} memorias registradas`}>
            <div className="memory-orbit" aria-hidden="true">
              <HardDrive />
              <span />
            </div>
            <div>
              <span>Memoria persistente</span>
              <strong>{memoryCount.toString().padStart(2, "0")}</strong>
              <small>registros locais</small>
            </div>
          </section>

          <section className="capability-list" aria-label="Recursos disponiveis">
            <div><Search aria-hidden="true" /><span>Pesquisa web</span><strong>PRONTA</strong></div>
            <div><BrainCircuit aria-hidden="true" /><span>IA local</span><strong>{active ? "ATIVA" : "ESPERA"}</strong></div>
            <div><MonitorCog aria-hidden="true" /><span>Controle PC</span><strong>SEGURO</strong></div>
          </section>

          <section className="conversation-panel" aria-label="Conversa recente">
            <div className="panel-heading">
              <div><MessageSquareText aria-hidden="true" /><h2>Registro recente</h2></div>
              <span>{messages.length.toString().padStart(2, "0")}</span>
            </div>
            <div className="message-stream">
              {recentMessages.map((message) => (
                <article className={`message-entry message-entry--${message.role}`} key={message.id}>
                  <div className="message-meta">
                    <span>{messageLabel(message.role)}</span>
                    <time dateTime={message.createdAt}>
                      {new Date(message.createdAt).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </time>
                  </div>
                  <p>{message.text}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="source-list">
                      <span><Globe2 aria-hidden="true" /> Fontes</span>
                      <ul>
                        {message.sources.slice(0, 3).map((source) => (
                          <li key={source.url}>
                            {source.url.startsWith("knowledge://") ? (
                              <span className="source-document"><HardDrive aria-hidden="true" /><span>{source.title}</span></span>
                            ) : (
                              <a
                                href={source.url}
                                onClick={(event) => {
                                  event.preventDefault();
                                  void openUrl(source.url);
                                }}
                                rel="noreferrer"
                                target="_blank"
                              >
                                <ExternalLink aria-hidden="true" /><span>{source.title}</span>
                              </a>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </article>
              ))}
              {recentMessages.length === 0 && (
                <div className="stream-empty"><Radio aria-hidden="true" /><span>Sem atividade</span></div>
              )}
            </div>
          </section>
        </aside>

        <footer className="command-footer">
          <StatusDot active={microphoneActive} label="Audio" />
          <div className="footer-track" aria-hidden="true"><span /></div>
          <StatusDot active={connected} label="Core" />
          <StatusDot active={memoryCount > 0} label="Memoria" />
          <StatusDot active label="Pesquisa" />
          <Wifi className={connected ? "footer-icon--active" : ""} aria-hidden="true" />
        </footer>
      </div>
    </main>
  );
}
