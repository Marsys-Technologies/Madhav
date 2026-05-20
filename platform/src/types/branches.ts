export interface ConversationBranch {
  id: string
  conversationId: string
  editedMessageId: string
  parentBranchId: string | null
  snapshotJsonb: Record<string, unknown>
  createdAt: string // ISO timestamp
}
