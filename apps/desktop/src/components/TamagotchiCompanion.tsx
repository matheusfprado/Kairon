import clsx from "clsx";
import { Heart } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";
import type { KaironState } from "../types/kairon";

interface TamagotchiCompanionProps {
  state: KaironState;
  transcript?: string;
  response?: string;
  dragHandleProps?: ButtonHTMLAttributes<HTMLButtonElement>;
}

export function TamagotchiCompanion({ state, dragHandleProps }: TamagotchiCompanionProps) {
  return (
    <section className={clsx("tamagotchi", `tamagotchi--${state}`)} aria-label="Companheiro Kairon">
      <div className="tamagotchi__halo" aria-hidden="true" />
      {dragHandleProps ? (
        <button type="button" className="tamagotchi__body" aria-label="Mover mascote; arraste ou use as setas" {...dragHandleProps}>
          <img src="/kairon-companion.png" alt="Kairon, robô companheiro" draggable={false} />
        </button>
      ) : (
        <div className="tamagotchi__body"><img src="/kairon-companion.png" alt="Kairon, robô companheiro" /><div className="tamagotchi__heart" aria-hidden="true"><Heart /></div></div>
      )}
      <div className="tamagotchi__name"><span>K</span> KAIRON <small>companheiro local</small></div>
    </section>
  );
}
