/**
 * D4 Graph Wave — per-wave registration file (Gate A compliant)
 * ==============================================================
 * Registers the traverse_chart_graph capability introduced in the D4 wave.
 *
 * GATE A: This file is the ONLY new file that touches registry state for D4.
 * The central registry/index.ts and registry/types.ts are NOT edited by this wave.
 *
 * To activate: import this file from your app bootstrap or the L2 layer index.
 * The import has a side-effect: it calls registerCapability for D4's capability.
 *
 * Wave: D4 (CGM graph traversal)
 * Created: 2026-06-28
 */

import { registerCapability } from '../../index'
import { traverseChartGraphCapability } from './traverse_chart_graph'

registerCapability(traverseChartGraphCapability)
