import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, RotateCcw, ArrowLeft, Loader2, Sparkles, User, AlertCircle } from 'lucide-react';

interface ChatAssistantProps {
  user: any;
  onRefreshDashboard: () => void;
}

const STATES_META: Record<string, { label: string; progress: number }> = {
  "HOME_MENU": { label: "Home Menu", progress: 5 },
  "PRODUCT_CATEGORY": { label: "Product Category", progress: 15 },
  "PRODUCT_MODEL": { label: "Product Model", progress: 25 },
  "PRODUCT_PURCHASE_DATE": { label: "Purchase Date", progress: 35 },
  "PRODUCT_WARRANTY": { label: "Warranty Status", progress: 45 },
  "PRODUCT_SERIAL": { label: "Serial Number", progress: 55 },
  "PRODUCT_INSTALL_DATE": { label: "Installation Date", progress: 65 },
  "ISSUE_COLLECTION": { label: "Issue Details", progress: 75 },
  "CONFIRM_DETAILS_BEFORE_BOOKING": { label: "Review Details", progress: 85 },
  "SERVICE_ADDRESS": { label: "Service Address", progress: 90 },
  "SERVICE_SCHEDULE": { label: "Appointment Date & Time", progress: 95 },
  "BOOKING_CONFIRMATION": { label: "Booking Confirmed", progress: 100 },
  "ORDER_LOOKUP": { label: "Order Lookup", progress: 30 },
  "ORDER_STATUS_DISPLAY": { label: "Order Status Timeline", progress: 70 },
  "ORDER_COMPLAINT_FORM": { label: "Submit Complaint", progress: 90 },
  "ORDER_CALLBACK_CONFIRM": { label: "Callback Requested", progress: 100 },
  "ORDER_ESCALATE_CONFIRM": { label: "Escalated to Support", progress: 100 },
  "OTHER_HELP_MENU": { label: "Other Services", progress: 25 },
  "OTHER_WARRANTY_INFO": { label: "Warranty & AMC Information", progress: 60 },
  "OTHER_PROD_REGISTRATION": { label: "Product Registration", progress: 60 },
  "OTHER_INSTALL_REQUEST": { label: "Request Installation", progress: 60 },
  "OTHER_BILL_HELP": { label: "Billing & Invoices Help", progress: 60 },
  "OTHER_CANCEL_RETURN": { label: "Cancellation / Return Request", progress: 60 },
  "OTHER_FEEDBACK": { label: "Submit Feedback", progress: 60 },
  "OTHER_COMPLAINT": { label: "Escalate Complaint", progress: 60 },
  "OTHER_FAQ": { label: "Frequently Asked Questions", progress: 60 },
  "TICKET_SUBMITTED": { label: "Request Submitted", progress: 100 }
};

const CATEGORIES = ["Refrigerator", "Washing Machine", "Microwave", "Dishwasher", "AC", "TV", "Others"];

const CATEGORY_ISSUES: Record<string, string[]> = {
  "Refrigerator": ["Not cooling", "Leaking water", "Making noise", "Door not closing", "Ice maker not working", "Other"],
  "Washing Machine": ["Not turning on", "Spin cycle not working", "Leaking water", "Making noise", "Error code displayed", "Other"],
  "Microwave": ["Not heating", "Turntable not spinning", "Sparking inside", "Touchpad unresponsive", "Other"],
  "Dishwasher": ["Leaking water", "Not draining", "Loud noise", "Dishes not clean", "Other"],
  "AC": ["Not cooling", "Leaking water", "Blowing warm air", "Remote not working", "Other"],
  "TV": ["No screen display", "Sound but no picture", "Lines on screen", "Remote unresponsive", "Other"],
  "Others": ["Not turning on", "Leaking water", "Making noise", "Error code displayed", "Other"]
};

export const ChatAssistant: React.FC<ChatAssistantProps> = ({ user, onRefreshDashboard }) => {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [textInput, setTextInput] = useState('');
  const [dateInput, setDateInput] = useState('');
  const [checkInput, setCheckInput] = useState(false);
  const [selectInput, setSelectInput] = useState('');
  const [textInput2, setTextInput2] = useState('');
  const [textInput3, setTextInput3] = useState('');
  const [textInput4, setTextInput4] = useState('');
  const [textareaInput, setTextareaInput] = useState('');

  // FAQ mock list matching state
  const faqs = [
    { q: "How long is the standard warranty on appliances?", a: "appliances come with a standard 1-year parts and labor warranty. Some appliances like washing machine motors and refrigerator compressors have extended warranties of up to 10 years on the key part." },
    { q: "How can I reschedule my technician visit?", a: "You can easily reschedule your booking in the 'My Appointments' tab in this customer portal. Simply click the 'Reschedule' button, choose a new date and time slot, and click save." },
    { q: "Where do I find my appliance serial number?", a: "For refrigerators, the serial number is on a label inside the fresh food compartment on the side wall. For washing machines, it is inside the door or on the back. For TVs, it is on the back panel." },
    { q: "What should I do if my refrigerator is not cooling?", a: "1. Check if the door is fully closed.\n2. Ensure there is at least 2 inches of space around the unit for ventilation.\n3. Clean the condenser coils at the bottom/back.\n4. Check if the temperature settings are set correctly (recommended: 37°F for fridge, 0°F for freezer)." },
    { q: "Can I cancel my service appointment?", a: "Yes, you can cancel your appointment up to 2 hours before the scheduled time slot in the 'My Appointments' tab." }
  ];

  // Initialize or fetch session
  useEffect(() => {
    const initChat = async () => {
      setLoading(true);
      setErrorMsg('');
      try {
        // Look for active session in localStorage
        const storedSessionId = localStorage.getItem(`chat_sess_${user.user_id}`);
        let currentSession;
        if (storedSessionId) {
          try {
            currentSession = await api.chat.getSession(storedSessionId);
          } catch (e) {
            // session expired or missing in DB, create new
            currentSession = await api.chat.createSession(user.user_id);
          }
        } else {
          currentSession = await api.chat.createSession(user.user_id);
        }
        setSession(currentSession);
        localStorage.setItem(`chat_sess_${user.user_id}`, currentSession.session_id);
      } catch (err: any) {
        setErrorMsg('Failed to initialize support chatbot.');
      } finally {
        setLoading(false);
      }
    };
    initChat();
  }, [user.user_id]);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages, typing]);

  const handleAction = async (inputValue: any, displayStr: string) => {
    if (!session) return;
    setActionLoading(true);
    setTyping(true);
    setErrorMsg('');
    
    // Clear forms state
    setTextInput('');
    setDateInput('');
    setCheckInput(false);
    setSelectInput('');
    setTextInput2('');
    setTextInput3('');
    setTextInput4('');
    setTextareaInput('');

    try {
      const updatedSession = await api.chat.postMessage(session.session_id, inputValue, displayStr);
      
      // Artificial short delay for typing feel
      setTimeout(() => {
        setSession(updatedSession);
        setTyping(false);
        setActionLoading(false);
        // Refresh dashboard statistics if we completed booking / tickets
        const finalStates = ["BOOKING_CONFIRMATION", "TICKET_SUBMITTED", "ORDER_CALLBACK_CONFIRM", "ORDER_ESCALATE_CONFIRM"];
        if (finalStates.includes(updatedSession.current_state)) {
          onRefreshDashboard();
        }
      }, 600);

    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to submit response.');
      setTyping(false);
      setActionLoading(false);
    }
  };

  const handleBack = async () => {
    if (!session || actionLoading) return;
    setActionLoading(true);
    setErrorMsg('');
    try {
      const updatedSession = await api.chat.stepBack(session.session_id);
      setSession(updatedSession);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Cannot go back further.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestart = async () => {
    if (!session || actionLoading) return;
    if (!window.confirm('Are you sure you want to restart the chatbot assistant flow?')) return;
    setActionLoading(true);
    setErrorMsg('');
    try {
      const updatedSession = await api.chat.restart(session.session_id);
      setSession(updatedSession);
    } catch (err: any) {
      setErrorMsg('Failed to restart conversation.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-500 gap-3">
        <Loader2 className="w-8 h-8 text-brand-red animate-spin" />
        <p className="text-sm font-semibold">Initializing SmartCare Diagnostic Agent...</p>
      </div>
    );
  }

  const currentState = session?.current_state || "HOME_MENU";
  const stateMeta = STATES_META[currentState] || { label: "Chatting", progress: 50 };

  const renderActiveForm = () => {
    if (actionLoading) return null;

    switch (currentState) {
      case 'PRODUCT_MODEL':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction(textInput, `Model number: ${textInput}`);
          }} className="flex items-center gap-2 w-full">
            <input
              type="text"
              required
              placeholder="e.g. LFXS26973S"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg py-2.5 px-4 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
            />
            <button type="submit" className="btn-premium p-2.5 flex items-center justify-center shrink-0">
              <Send className="w-4 h-4" />
            </button>
          </form>
        );

      case 'PRODUCT_PURCHASE_DATE':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction(dateInput, `Purchase Date: ${dateInput}`);
          }} className="flex items-center gap-2 w-full">
            <input
              type="date"
              required
              max={new Date().toISOString().split('T')[0]}
              value={dateInput}
              onChange={(e) => setDateInput(e.target.value)}
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg py-2.5 px-4 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
            />
            <button type="submit" className="btn-premium p-2.5 flex items-center justify-center shrink-0">
              <Send className="w-4 h-4" />
            </button>
          </form>
        );

      case 'PRODUCT_SERIAL':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction(textInput, `Serial number: ${textInput}`);
          }} className="flex items-center gap-2 w-full">
            <input
              type="text"
              required
              placeholder="e.g. REF123456789 (min 5 chars)"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              className="flex-1 bg-gray-50 border border-gray-200 rounded-lg py-2.5 px-4 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
            />
            <button type="submit" className="btn-premium p-2.5 flex items-center justify-center shrink-0">
              <Send className="w-4 h-4" />
            </button>
          </form>
        );

      case 'PRODUCT_INSTALL_DATE':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            const val = checkInput ? dateInput : '';
            const display = checkInput ? `Installation Date: ${dateInput}` : 'Skipped installation date';
            handleAction(val, display);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200">
            <label className="flex items-center gap-2 text-xs font-semibold text-gray-700">
              <input
                type="checkbox"
                checked={checkInput}
                onChange={(e) => setCheckInput(e.target.checked)}
                className="rounded text-brand-red focus:ring-brand-red"
              />
              <span>Enter different installation date</span>
            </label>
            {checkInput && (
              <input
                type="date"
                required
                max={new Date().toISOString().split('T')[0]}
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            )}
            <button type="submit" className="btn-premium w-full">
              Continue
            </button>
          </form>
        );

      case 'ISSUE_COLLECTION':
        const cat = session?.chat_data?.category || "Others";
        const issueOptions = CATEGORY_ISSUES[cat] || ["Other"];
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ issue_option: selectInput || issueOptions[0], issue_description: textareaInput }, `Issue: ${selectInput || issueOptions[0]} (${textareaInput || 'None'})`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Common Symptoms</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              >
                {issueOptions.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Symptom Description (Required if &quot;Other&quot;)</label>
              <textarea
                placeholder="Describe details, error codes, noise symptoms..."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red h-20"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Submit Symptoms
            </button>
          </form>
        );

      case 'SERVICE_ADDRESS':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({
              address: textInput,
              city: textInput2,
              pincode: textInput3,
              phone: textInput4,
              notes: textareaInput
            }, `Service Address: ${textInput}, ${textInput2} - ${textInput3} (Phone: ${textInput4})`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Street Address *</label>
              <input
                type="text"
                required
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">City *</label>
                <input
                  type="text"
                  required
                  value={textInput2}
                  onChange={(e) => setTextInput2(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Pincode *</label>
                <input
                  type="text"
                  required
                  placeholder="5 or 6 digits"
                  value={textInput3}
                  onChange={(e) => setTextInput3(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Contact Phone *</label>
              <input
                type="text"
                required
                placeholder="10 to 15 digits"
                value={textInput4}
                onChange={(e) => setTextInput4(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Special Site Notes (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Ring bell, gate code 123"
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Proceed to Scheduling
            </button>
          </form>
        );

      case 'SERVICE_SCHEDULE':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({
              preferred_date: dateInput,
              preferred_time_slot: selectInput || '09:00 AM - 12:00 PM (Morning)'
            }, `Scheduled on ${dateInput} during ${selectInput || '09:00 AM - 12:00 PM (Morning)'}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Preferred Visit Date</label>
              <input
                type="date"
                required
                min={new Date().toISOString().split('T')[0]}
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Preferred Time Slot</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              >
                <option value="09:00 AM - 12:00 PM (Morning)">09:00 AM - 12:00 PM (Morning)</option>
                <option value="12:00 PM - 03:00 PM (Afternoon)">12:00 PM - 03:00 PM (Afternoon)</option>
                <option value="03:00 PM - 06:00 PM (Evening)">03:00 PM - 06:00 PM (Evening)</option>
              </select>
            </div>
            <button type="submit" className="btn-premium w-full">
              Confirm Service Appointment
            </button>
          </form>
        );

      case 'ORDER_LOOKUP':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ order_id: textInput, contact_info: textInput2 }, `Tracking Order ID: ${textInput} | Contact: ${textInput2}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Order ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. ORD-1153"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Registered Phone or Email *</label>
              <input
                type="text"
                required
                placeholder="e.g. jane.smith@support-example.com"
                value={textInput2}
                onChange={(e) => setTextInput2(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Lookup Shipment
            </button>
          </form>
        );

      case 'ORDER_COMPLAINT_FORM':
      case 'OTHER_COMPLAINT':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ subject: textInput, title: textInput, description: textareaInput }, `Complaint: ${textInput}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Complaint Topic / Title *</label>
              <input
                type="text"
                required
                placeholder="e.g. Shipped package damaged"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Detailed Description *</label>
              <textarea
                required
                placeholder="Provide details about symptoms, invoice issues, or shipping delays..."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red h-20"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Submit Ticket
            </button>
          </form>
        );

      case 'OTHER_WARRANTY_INFO':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ category: selectInput || CATEGORIES[0], comments: textareaInput }, `AMC quote request for ${selectInput || CATEGORIES[0]}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Product Category *</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm focus:outline-none"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Appliance Age / Notes</label>
              <textarea
                placeholder="e.g. Fridge is 2 years old, looking for 1 year AMC plan extension."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 h-16 text-sm focus:outline-none"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Request Quotation
            </button>
          </form>
        );

      case 'OTHER_PROD_REGISTRATION':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({
              category: selectInput || CATEGORIES[0],
              model_number: textInput,
              serial_number: textInput2,
              purchase_date: dateInput
            }, `Registering: ${selectInput || CATEGORIES[0]} (Model: ${textInput})`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Product Category *</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Model Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. LFXS269"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Serial Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. REF1234"
                  value={textInput2}
                  onChange={(e) => setTextInput2(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Purchase Date *</label>
              <input
                type="date"
                required
                max={new Date().toISOString().split('T')[0]}
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Register Appliance
            </button>
          </form>
        );

      case 'OTHER_INSTALL_REQUEST':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({
              category: selectInput || CATEGORIES[0],
              model_number: textInput,
              serial_number: textInput2,
              address: textareaInput,
              pincode: textInput3,
              preferred_date: dateInput
            }, `Installation for: ${selectInput || CATEGORIES[0]} on ${dateInput}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Category *</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Model Number *</label>
                <input
                  type="text"
                  required
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Serial (Optional)</label>
                <input
                  type="text"
                  placeholder="Leave empty if new"
                  value={textInput2}
                  onChange={(e) => setTextInput2(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Site Address *</label>
              <textarea
                required
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 h-14 text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Pincode *</label>
                <input
                  type="text"
                  required
                  value={textInput3}
                  onChange={(e) => setTextInput3(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Preferred Date *</label>
                <input
                  type="date"
                  required
                  min={new Date().toISOString().split('T')[0]}
                  value={dateInput}
                  onChange={(e) => setDateInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
            </div>
            <button type="submit" className="btn-premium w-full">
              Book Installation
            </button>
          </form>
        );

      case 'OTHER_BILL_HELP':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ order_id: textInput, subject: textInput2, message: textareaInput }, `Billing query: ${textInput2}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Order Ref ID</label>
                <input
                  type="text"
                  placeholder="e.g. ORD-9021"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Subject *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Double charged invoice"
                  value={textInput2}
                  onChange={(e) => setTextInput2(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Message Details *</label>
              <textarea
                required
                placeholder="Explain the billing or charge issue..."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 h-16 text-sm"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Submit Billing Ticket
            </button>
          </form>
        );

      case 'OTHER_CANCEL_RETURN':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ order_id: textInput, request_type: selectInput || 'Cancellation', reason: textareaInput }, `${selectInput || 'Cancellation'} Request for order ${textInput}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Order ID *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ORD-9021"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Request Type *</label>
                <select
                  value={selectInput}
                  onChange={(e) => setSelectInput(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-lg p-2 text-sm"
                >
                  <option value="Cancellation">Cancellation</option>
                  <option value="Return">Return</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Reason for Request *</label>
              <textarea
                required
                placeholder="Please explain why you want to cancel or return..."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 h-16 text-sm"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Submit Cancellation/Return
            </button>
          </form>
        );

      case 'OTHER_FEEDBACK':
        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleAction({ rating: selectInput || '5 Star', comments: textareaInput }, `Submitted feedback rating: ${selectInput || '5 Star'}`);
          }} className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Experience Rating</label>
              <select
                value={selectInput}
                onChange={(e) => setSelectInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 text-sm"
              >
                <option value="5 Star">⭐⭐⭐⭐⭐ (5 Star - Excellent)</option>
                <option value="4 Star">⭐⭐⭐⭐ (4 Star - Good)</option>
                <option value="3 Star">⭐⭐⭐ (3 Star - Average)</option>
                <option value="2 Star">⭐⭐ (2 Star - Poor)</option>
                <option value="1 Star">⭐ (1 Star - Very Unsatisfactory)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Additional comments</label>
              <textarea
                placeholder="Your review comments..."
                value={textareaInput}
                onChange={(e) => setTextareaInput(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2.5 h-16 text-sm"
              />
            </div>
            <button type="submit" className="btn-premium w-full">
              Submit Feedback
            </button>
          </form>
        );

      case 'OTHER_FAQ':
        return (
          <div className="w-full space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-left max-h-[220px] overflow-y-auto pr-1">
            <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Help Articles</h4>
            {faqs.map((faq, idx) => (
              <details key={idx} className="group bg-white border border-gray-100 rounded-lg p-3 text-xs select-none cursor-pointer">
                <summary className="font-semibold text-gray-800 flex items-center justify-between list-none">
                  <span>❓ {faq.q}</span>
                  <span className="text-gray-400 group-open:rotate-180 transition-transform">&darr;</span>
                </summary>
                <p className="text-gray-600 mt-2 whitespace-pre-line border-t border-gray-50 pt-2">{faq.a}</p>
              </details>
            ))}
            <button 
              type="button" 
              onClick={() => handleAction('Home', 'Go back to Home')}
              className="btn-premium w-full mt-2"
            >
              🏠 Back to Home Menu
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  const getRoleBubbleColor = (role: string) => {
    return role === 'assistant' 
      ? 'bg-gray-100 text-gray-800 rounded-bl-none shadow-sm' 
      : 'bg-brand-red text-white rounded-br-none shadow-premium self-end ml-auto';
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col h-[calc(100vh-140px)] overflow-hidden">
      {/* Chat Sub-Header */}
      <div className="bg-white border-b border-gray-100 p-4 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-brand-red/10 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-brand-red" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-800">{stateMeta.label}</h3>
            <div className="w-24 bg-gray-100 rounded-full h-1.5 mt-1 overflow-hidden">
              <div 
                className="bg-brand-red h-full rounded-full transition-all duration-300"
                style={{ width: `${stateMeta.progress}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Back and Restart Controls */}
        <div className="flex gap-1.5">
          <button
            onClick={handleBack}
            disabled={actionLoading || !session?.state_history?.length}
            className="flex items-center justify-center p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:pointer-events-none transition-colors border border-gray-100 shadow-sm"
            title="Go Back one step"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleRestart}
            disabled={actionLoading}
            className="flex items-center justify-center p-2 rounded-lg text-gray-400 hover:text-brand-red hover:bg-red-50 disabled:opacity-40 disabled:pointer-events-none transition-colors border border-gray-100 shadow-sm"
            title="Restart diagnostic assistant"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-gray-50/50">
        <AnimatePresence initial={false}>
          {session?.messages?.map((msg: any, idx: number) => {
            const isBot = msg.role === 'assistant';
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex gap-3 max-w-[85%] ${isBot ? '' : 'ml-auto justify-end'}`}
              >
                {isBot && (
                  <div className="w-8 h-8 rounded-full bg-brand-red flex items-center justify-center text-white shrink-0 shadow-sm">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                )}
                
                <div className="flex flex-col gap-2">
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${getRoleBubbleColor(msg.role)}`}>
                    {/* Render message HTML formatting cleanly */}
                    <div 
                      dangerouslySetInnerHTML={{ 
                        __html: msg.content
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/### (.*?)\n/g, '<h4 class="font-bold text-sm my-1 text-gray-800">$1</h4>')
                      }} 
                    />
                  </div>

                  {/* Suggest Quick action buttons */}
                  {isBot && msg.buttons && msg.buttons.length > 0 && idx === session.messages.length - 1 && !actionLoading && (
                    <div className="flex flex-wrap gap-2 mt-2 pl-1">
                      {msg.buttons.map((btn: any, btnIdx: number) => (
                        <button
                          key={btnIdx}
                          onClick={() => handleAction(btn.value, btn.label)}
                          className="bg-white border border-gray-200 text-gray-700 hover:border-brand-red hover:text-brand-red py-2 px-4 rounded-xl text-xs font-semibold shadow-sm hover:shadow active:scale-[0.98] transition-all"
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {!isBot && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 shrink-0 shadow-sm border border-gray-300">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Typing indicator */}
        {typing && (
          <div className="flex gap-3 max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-brand-red flex items-center justify-center text-white shrink-0 shadow-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 text-gray-800 rounded-2xl rounded-bl-none p-4 shadow-sm flex items-center gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="bg-red-50 text-brand-red text-xs p-3 border-t border-b border-red-100 flex items-center gap-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Dynamic Form Panel */}
      <div className="bg-white border-t border-gray-100 p-4 shrink-0 shadow-inner flex flex-col items-center">
        {renderActiveForm()}

        {/* Info label if no inputs required */}
        {(!renderActiveForm() && !actionLoading && (!session?.messages[session.messages.length - 1]?.buttons?.length)) && (
          <span className="text-xs text-gray-400 font-medium">Use the action buttons suggested above to reply to the assistant.</span>
        )}

        {actionLoading && (
          <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
            <Loader2 className="w-4 h-4 animate-spin text-brand-red" />
            <span>Processing transition...</span>
          </div>
        )}
      </div>
    </div>
  );
};
