import clsx from "clsx";
import { AudioLines, Mic } from "lucide-react";
import type { KaironState } from "../types/kairon";

interface VoiceCoreProps {
  state: KaironState;
}

const activeStates: KaironState[] = [
  "listening_for_wake_word",
  "wake_word_detected",
  "listening",
];

export function VoiceCore({ state }: VoiceCoreProps) {
  const listening = activeStates.includes(state);
  const speaking = state === "speaking";

  return (
    <div
      className={clsx(
        "voice-core",
        listening && "voice-core--listening",
        speaking && "voice-core--speaking",
        state === "error" && "voice-core--error",
      )}
      aria-hidden="true"
    >
      <span className="voice-core__ring voice-core__ring--outer" />
      <span className="voice-core__ring voice-core__ring--inner" />
      <div className="voice-core__surface">
        {speaking ? <AudioLines className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
      </div>
      <div className="voice-core__meter">
        {Array.from({ length: 7 }, (_, index) => (
          <span key={index} />
        ))}
      </div>
    </div>
  );
}
