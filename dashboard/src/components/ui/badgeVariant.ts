import type { Variant } from "./Badge";

export function badgeVariant(name: string): Variant {
  const map: Record<string, Variant> = {
    nma: "amber",
    cra: "red",
    aaa: "purple",
    mda: "red",
    bfi: "red",
    tdp: "amber",
    rl: "cyan",
    drl: "blue",
    marl: "green",
    none: "muted",
    tdcb: "blue",
    pbft: "cyan",
    static_dpos: "purple",
    majority: "amber",
    random: "muted",
  };
  return map[name.toLowerCase()] ?? "muted";
}
