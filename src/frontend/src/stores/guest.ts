import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface GuestTemplate {
  id: number
  name: string
  persona: string
  system_prompt: string
  speak_style: string
  avatar: string | null
}

export const useGuestStore = defineStore('guest', () => {
  const guestTemplates = ref<GuestTemplate[]>([])
  const activeGuests = ref<GuestTemplate[]>([])

  async function fetchGuests() {
    const res = await fetch('/api/guests')
    guestTemplates.value = await res.json()
  }

  async function createGuest(data: Partial<GuestTemplate>) {
    const res = await fetch('/api/guests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const guest = await res.json()
    guestTemplates.value.unshift(guest)
    return guest
  }

  async function deleteGuest(id: number) {
    await fetch(`/api/guests/${id}`, { method: 'DELETE' })
    guestTemplates.value = guestTemplates.value.filter(g => g.id !== id)
  }

  return { guestTemplates, activeGuests, fetchGuests, createGuest, deleteGuest }
})
