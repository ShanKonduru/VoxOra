import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * sessionStore — voice session state shared across components.
 */
export const useSessionStore = create(
  persist(
    (set) => ({
      wsStatus: 'idle',
      currentQuestion: null,
      questionIndex: 0,
      totalQuestions: 0,
      isCompleted: false,

      setWsStatus: (status) => set({ wsStatus: status }),
      setCurrentQuestion: (text, index, total) =>
        set({ currentQuestion: text, questionIndex: index, totalQuestions: total }),
      setCompleted: () => set({ isCompleted: true }),
      reset: () =>
        set({
          wsStatus: 'idle',
          currentQuestion: null,
          questionIndex: 0,
          totalQuestions: 0,
          isCompleted: false,
        }),
    }),
    {
      name: 'voxora-session',
      partialize: (state) => ({
        // Do not persist WebSocket state — only minimal session context
        questionIndex: state.questionIndex,
        totalQuestions: state.totalQuestions,
      }),
    }
  )
)
