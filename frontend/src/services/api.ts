import axios from 'axios';

// Vite proxy handles redirect to http://localhost:8000
const API_BASE = '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Auth
  auth: {
    login: async (username: string, password: string) => {
      const res = await client.post('/auth/login', { username, password });
      return res.data;
    },
    register: async (data: any) => {
      const res = await client.post('/auth/register', data);
      return res.data;
    },
  },

  // Users / Dashboard
  users: {
    getDashboard: async (userId: string) => {
      const res = await client.get(`/users/${userId}/dashboard`);
      return res.data;
    },
    registerProduct: async (userId: string, productData: any) => {
      const res = await client.post(`/users/${userId}/products`, productData);
      return res.data;
    },
  },

  // Orders
  orders: {
    lookup: async (orderId: string, contactInfo: string) => {
      const res = await client.get('/orders/lookup', {
        params: { order_id: orderId, contact_info: contactInfo },
      });
      return res.data;
    },
    requestCallback: async (orderId: string, userId: string) => {
      const res = await client.post(`orders/${orderId}/callback`, null, {
        params: { user_id: userId },
      });
      return res.data;
    },
    escalate: async (orderId: string, userId: string) => {
      const res = await client.post(`orders/${orderId}/escalate`, null, {
        params: { user_id: userId },
      });
      return res.data;
    },
    submitComplaint: async (orderId: string, userId: string, subject: string, description: string) => {
      const res = await client.post(`orders/${orderId}/complaint`, {
        title: subject,
        description: description,
        category: 'Complaint escalation'
      }, {
        params: { user_id: userId }
      });
      return res.data;
    }
  },

  // Appointments
  appointments: {
    reschedule: async (appointmentId: string, date: string, slot: string) => {
      const res = await client.put(`/appointments/${appointmentId}/reschedule`, {
        preferred_date: date,
        preferred_time_slot: slot,
      });
      return res.data;
    },
    cancel: async (appointmentId: string) => {
      const res = await client.put(`/appointments/${appointmentId}/cancel`);
      return res.data;
    },
  },

  // Support Tickets
  tickets: {
    create: async (userId: string, data: { title: string; description: string; category: string }) => {
      const res = await client.post('/support-cases', data, {
        params: { user_id: userId },
      });
      return res.data;
    },
  },

  // FSM Chat
  chat: {
    createSession: async (userId: string) => {
      const res = await client.post('/chat/session', null, {
        params: { user_id: userId },
      });
      return res.data;
    },
    getSession: async (sessionId: string) => {
      const res = await client.get(`/chat/session/${sessionId}`);
      return res.data;
    },
    postMessage: async (sessionId: string, inputValue: any, userDisplayStr: string) => {
      const res = await client.post(`/chat/session/${sessionId}/message`, {
        input_value: inputValue,
        user_display_str: userDisplayStr,
      });
      return res.data;
    },
    postVoiceMessage: async (sessionId: string, audioBlob: Blob) => {
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice_input.webm');
      const res = await client.post(`/chat/session/${sessionId}/voice`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return res.data;
    },
    stepBack: async (sessionId: string) => {
      const res = await client.post(`/chat/session/${sessionId}/back`);
      return res.data;
    },
    restart: async (sessionId: string) => {
      const res = await client.post(`/chat/session/${sessionId}/restart`);
      return res.data;
    },
  },
};
