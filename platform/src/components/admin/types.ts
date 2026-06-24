export interface AdminAccessRequest {
  id: string
  full_name: string
  email: string
  reason: string | null
  status: 'pending' | 'approved' | 'rejected'
  requested_at: string
  reviewed_at: string | null
  approved_user_id: string | null
  approved_username: string | null
  approved_name: string | null
}

export interface AdminUser {
  id: string
  role: 'super_admin' | 'guest'
  status: 'pending' | 'active' | 'disabled'
  name: string | null
  username: string | null
  email: string | null
  created_at: string
  approved_at: string | null
}

export interface AdminChart {
  id: string
  name: string
  subject_name: string | null
  birth_date: string
  birth_place: string
  owner_id: string
  owner_username: string | null
  owner_name: string | null
  grant_count: number
}

export interface AdminChartGrant {
  id: string
  subject_name: string | null
  birth_date: string
  birth_place: string
  owner_id: string
  owner_username: string | null
  is_own: boolean
  granted: boolean
}
