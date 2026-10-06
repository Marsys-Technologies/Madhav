import { z } from "zod";
import { STACK_ROUTING } from "@/lib/models/registry";
export const personaSchema = z
  .object({
    name: z.string().trim().min(1).max(50),
    system_prompt: z.string().trim().min(1).max(4000),
    default_style: z.enum(["acharya", "brief", "client"]).nullable().optional(),
    default_stack: z
      .string()
      .refine((s) => Object.prototype.hasOwnProperty.call(STACK_ROUTING, s))
      .nullable()
      .optional(),
    is_default: z.boolean().optional(),
  })
  .strict();
export const personaPatchSchema = personaSchema
  .partial()
  .refine((v) => Object.keys(v).length > 0);
