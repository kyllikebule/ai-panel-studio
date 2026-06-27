import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Discussion {
  id: number
  topic: string
  status: string
  host_name: string
  max_rounds: number
  current_round: number
  created_at: string
  guest_count?: number
}

export const useDiscussionStore = defineStore('discussion', () => {
  const discussions = ref<Discussion[]>([])
  const currentDiscussion = ref<Discussion | null>(null)
  const messages = ref<any[]>([])
  const opinions = ref<any[]>([])

  async function fetchDiscussions() {
    const res = await fetch('/api/discussions')
    discussions.value = await res.json()
  }

  async function createDiscussion(data: any) {
    const res = await fetch('/api/discussions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    currentDiscussion.value = await res.json()
    return currentDiscussion.value
  }

  async function loadDiscussion(id: number) {
    const res = await fetch(`/api/discussions/${id}`)
    currentDiscussion.value = await res.json()
  }

  return { discussions, currentDiscussion, messages, opinions, fetchDiscussions, createDiscussion, loadDiscussion }
})
