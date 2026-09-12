import { isTauri } from "@tauri-apps/api/core";
import { LogicalPosition } from "@tauri-apps/api/dpi";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { GripHorizontal, X } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { TamagotchiCompanion } from "../components/TamagotchiCompanion";
import { useKaironSocket } from "../hooks/useKaironSocket";
import { useKaironStore } from "../stores/kaironStore";

const statusLabel = {
  idle: "Preparando o microfone", listening_for_wake_word: "Estou ouvindo", wake_word_detected: "Pode continuar",
  listening: "Estou ouvindo", processing: "Entendi você", thinking: "Estou pensando", speaking: "Respondendo",
  executing: "Executando", error: "Não consegui responder", offline: "Reconectando",
} as const;

export function CompanionPage() {
  useKaironSocket(true, true);
  const { state } = useKaironStore();
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const dragging = useRef<{ x: number; y: number } | null>(null);
  const widget = useRef<HTMLElement>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const fit = () => setPosition((current) => ({
      x: Math.max(0, Math.min(current.x, window.innerWidth - (widget.current?.offsetWidth ?? 320))),
      y: Math.max(0, Math.min(current.y, window.innerHeight - (widget.current?.offsetHeight ?? 480))),
    }));
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  function move(x: number, y: number) {
    setPosition({
      x: Math.max(0, Math.min(x, window.innerWidth - (widget.current?.offsetWidth ?? 320))),
      y: Math.max(0, Math.min(y, window.innerHeight - (widget.current?.offsetHeight ?? 480))),
    });
  }

  function startDrag(event: PointerEvent<HTMLButtonElement>) {
    if (event.button !== 0) return;
    if (isTauri()) {
      void getCurrentWindow().startDragging().catch(() => setNotice("Não consegui mover a janela."));
      return;
    }
    dragging.current = { x: event.clientX - position.x, y: event.clientY - position.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  async function keyboardMove(event: KeyboardEvent<HTMLButtonElement>) {
    const offset: Record<string, [number, number]> = {
      ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20],
    };
    const [x, y] = offset[event.key] ?? [];
    if (x === undefined || y === undefined) return;
    event.preventDefault();
    if (isTauri()) {
      try {
        const current = getCurrentWindow();
        const point = (await current.outerPosition()).toLogical(await current.scaleFactor());
        await current.setPosition(new LogicalPosition(point.x + x, point.y + y));
      } catch { setNotice("Não consegui mover a janela."); }
    } else move(position.x + x, position.y + y);
  }

  const dragProps = {
    onPointerDown: startDrag,
    onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => void keyboardMove(event),
    onPointerMove: (event: PointerEvent<HTMLButtonElement>) => {
      if (dragging.current) move(event.clientX - dragging.current.x, event.clientY - dragging.current.y);
    },
    onPointerUp: () => { dragging.current = null; },
    onPointerCancel: () => { dragging.current = null; },
    onLostPointerCapture: () => { dragging.current = null; },
  };

  return (
    <main ref={widget} className="companion-widget" data-state={state}
      style={{ transform: `translate(${position.x}px, ${position.y}px)` }}>
      <header className="companion-toolbar">
        <button type="button" className="companion-drag" aria-label="Arrastar Kairon; use as setas para mover" {...dragProps}>
          <GripHorizontal aria-hidden="true" /> Kairon
        </button>
        <span className="companion-status" role="status" aria-live="polite">{statusLabel[state]}</span>
        {isTauri() && <button type="button" aria-label="Fechar Kairon" onClick={() => {
          void getCurrentWindow().close().catch(() => setNotice("Não consegui fechar a janela."));
        }}><X aria-hidden="true" /></button>}
      </header>
      <TamagotchiCompanion state={state} dragHandleProps={dragProps} />
      <p className="companion-voice-hint">Diga “Kairon” e faça seu pedido.</p>
      {notice && <p className="companion-error" role="alert">{notice}</p>}
    </main>
  );
}
