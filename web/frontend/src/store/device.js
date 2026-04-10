import { defineStore } from 'pinia'

export const useDeviceStore = defineStore('device', {
  state: () => ({
    deviceStatus: null,
    commStatus: [],
    environment: null,
    power: null,
    websocketConnected: false
  }),

  actions: {
    setDeviceStatus(status) {
      this.deviceStatus = status
    },

    setCommStatus(status) {
      this.commStatus = status
    },

    setEnvironment(data) {
      this.environment = data
    },

    setPower(data) {
      this.power = data
    },

    setWebSocketConnected(connected) {
      this.websocketConnected = connected
    }
  }
})
