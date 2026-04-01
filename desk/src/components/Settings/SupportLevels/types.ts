export const SupportLevelListResourceSymbol = Symbol("SupportLevelListResource");

export interface SupportLevel {
  name: string;
  level_name: string;
  level_order: number;
  display_name?: string;
  color?: string;
  allow_escalation_to_next: number;
  auto_escalate_on_breach: number;
  auto_escalate_minutes?: number;
}
