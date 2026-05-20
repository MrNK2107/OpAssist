export interface Opportunity {
  id: string
  title: string
  type: string
  url: string
  source: string
  description: string
  organizer: string
  deadline: string | null
  location: string
  prize: string
  tags: string[]
  difficulty: string
  is_closed: boolean
  image_url: string | null
}
