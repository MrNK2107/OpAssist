export type VerticalType = 'hackathon' | 'internship' | 'job' | 'scholarship' | 'oss' | 'ambassador' | 'event'

export interface Opportunity {
  id: string
  title: string
  type: VerticalType
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
