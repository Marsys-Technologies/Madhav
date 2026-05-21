// IntraSignalDetector — stub for ICR stream
// ICR-S1: interface + empty class skeleton (2026-05-21)
// Implementation: ICR-S3

import type { ConflictRecord } from './types';

export interface DetectorConfig {
  msr_path: string;
  forensic_path: string;
}

export class IntraSignalDetector {
  constructor(private config: DetectorConfig) {}

  /**
   * Detect Class A conflicts: a signal's claim disagrees with its cited FORENSIC sources.
   * Implementation deferred to ICR-S3.
   */
  async detectClassA(): Promise<ConflictRecord[]> {
    throw new Error('Not implemented — ICR-S3');
  }

  /**
   * Detect Class B conflicts: two signals make incompatible claims about the same chart point.
   * Implementation deferred to ICR-S3.
   */
  async detectClassB(): Promise<ConflictRecord[]> {
    throw new Error('Not implemented — ICR-S3');
  }

  /**
   * Detect Class C conflicts: a signal's interpretation contradicts the synthesis layer.
   * Implementation deferred to ICR-S3.
   */
  async detectClassC(): Promise<ConflictRecord[]> {
    throw new Error('Not implemented — ICR-S3');
  }

  /**
   * Run all detectors and return combined conflict list.
   * Implementation deferred to ICR-S3.
   */
  async detectAll(): Promise<ConflictRecord[]> {
    throw new Error('Not implemented — ICR-S3');
  }
}
