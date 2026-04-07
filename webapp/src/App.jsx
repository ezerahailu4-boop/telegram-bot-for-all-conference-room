import React, { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';

const SUPABASE_URL = 'https://kwfrnqampjsxlxlghtfg.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3ZnJucWFtcGpzeGx4bGdodGZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjQ3ODIsImV4cCI6MjA5MDcwMDc4Mn0.q2rYdKH4d0fWRgYfyRXU0_rHxan2GaoHBGfo-zop_Cs';

async function supabaseInsert(payload) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/bookings`, {
    method: 'POST',
    headers: {
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const rooms = [
  { id: 'A', label: '3rd Floor Conference Room (Big)', emoji: '🏢' },
  { id: 'B', label: '3rd Floor Conference Room (Small)', emoji: '🏛️' },
  { id: 'C', label: '7th Floor Conference Room', emoji: '🏬' },
];

const timeSlots = [
  '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
  '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
  '17:00', '17:30', '18:00',
];

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #fff; overscroll-behavior: none; }
  .app { min-height: 100vh; padding: 20px 16px 32px; background: radial-gradient(ellipse at top, #1a0533 0%, #0a0a0f 60%); }
  .header { text-align: center; padding: 24px 0 32px; }
  .header-icon { width: 64px; height: 64px; background: linear-gradient(135deg, #7c3aed, #2563eb); border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin: 0 auto 16px; box-shadow: 0 8px 32px rgba(124,58,237,0.4); }
  .header-title { font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: -0.5px; }
  .header-sub { font-size: 13px; color: #6b7280; margin-top: 6px; font-weight: 500; }
  .menu-grid { display: flex; flex-direction: column; gap: 12px; }
  .menu-card { background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 24px; cursor: pointer; transition: transform 0.2s, border-color 0.2s; position: relative; overflow: hidden; }
  .menu-card:active { transform: scale(0.98); }
  .menu-card.quick { border-color: rgba(124,58,237,0.3); }
  .menu-card.schedule { border-color: rgba(37,99,235,0.3); }
  .card-top { display: flex; align-items: center; gap: 14px; margin-bottom: 10px; }
  .card-emoji { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
  .card-emoji.purple { background: linear-gradient(135deg, #7c3aed, #5b21b6); box-shadow: 0 4px 16px rgba(124,58,237,0.4); }
  .card-emoji.blue { background: linear-gradient(135deg, #2563eb, #1d4ed8); box-shadow: 0 4px 16px rgba(37,99,235,0.4); }
  .card-title { font-size: 17px; font-weight: 700; }
  .card-badge { font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 20px; margin-left: auto; }
  .badge-instant { background: rgba(124,58,237,0.2); color: #a78bfa; border: 1px solid rgba(124,58,237,0.3); }
  .badge-approval { background: rgba(37,99,235,0.2); color: #93c5fd; border: 1px solid rgba(37,99,235,0.3); }
  .card-desc { font-size: 13px; color: #6b7280; line-height: 1.5; padding-left: 62px; }
  .info-footer { text-align: center; margin-top: 24px; font-size: 12px; color: #374151; }
  .page { animation: fadeIn 0.2s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .back-btn { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: #9ca3af; font-size: 13px; font-weight: 500; padding: 8px 14px; border-radius: 10px; cursor: pointer; margin-bottom: 20px; transition: background 0.2s; }
  .back-btn:hover { background: rgba(255,255,255,0.1); }
  .page-header { margin-bottom: 24px; }
  .page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .page-sub { font-size: 13px; color: #6b7280; margin-top: 4px; }
  .section { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 18px; margin-bottom: 12px; }
  .section-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; }
  .input { width: 100%; padding: 12px 14px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; color: #fff; font-size: 14px; font-family: inherit; outline: none; transition: border-color 0.2s; -webkit-appearance: none; }
  .input:focus { border-color: rgba(124,58,237,0.5); }
  .input::placeholder { color: #4b5563; }
  .time-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .time-slot { padding: 9px 4px; text-align: center; border-radius: 10px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.07); cursor: pointer; font-size: 12px; font-weight: 500; color: #9ca3af; transition: all 0.15s; }
  .time-slot:hover { border-color: rgba(124,58,237,0.4); color: #fff; }
  .time-slot.selected { background: linear-gradient(135deg, #7c3aed, #2563eb); border-color: transparent; color: #fff; box-shadow: 0 2px 12px rgba(124,58,237,0.4); }
  .room-grid { display: flex; flex-direction: column; gap: 8px; }
  .room-option { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; cursor: pointer; font-size: 14px; font-weight: 500; color: #9ca3af; transition: all 0.15s; }
  .room-option:hover { border-color: rgba(124,58,237,0.4); color: #fff; }
  .room-option.selected { background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2)); border-color: rgba(124,58,237,0.6); color: #fff; box-shadow: 0 2px 12px rgba(124,58,237,0.3); }
  .room-option-emoji { font-size: 18px; }
  .btn { width: 100%; padding: 15px; border: none; border-radius: 14px; font-size: 15px; font-weight: 700; cursor: pointer; font-family: inherit; transition: transform 0.15s, box-shadow 0.15s; letter-spacing: 0.2px; }
  .btn:active { transform: scale(0.98); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary { background: linear-gradient(135deg, #7c3aed, #2563eb); color: #fff; box-shadow: 0 4px 20px rgba(124,58,237,0.4); }
  .btn-danger { background: linear-gradient(135deg, #dc2626, #b91c1c); color: #fff; box-shadow: 0 4px 20px rgba(220,38,38,0.35); }
  .btn-schedule { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; box-shadow: 0 4px 20px rgba(37,99,235,0.4); }
  .booked-card { background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.05)); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px; padding: 24px; margin-bottom: 16px; }
  .booked-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #10b981; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
  .booked-topic { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
  .booked-meta { font-size: 13px; color: #6b7280; display: flex; gap: 12px; flex-wrap: wrap; }
  .booked-meta span { display: flex; align-items: center; gap: 4px; }
  .quick-idle { text-align: center; padding: 16px 16px 0; }
  .quick-idle-icon { width: 80px; height: 80px; border-radius: 24px; background: linear-gradient(135deg, #7c3aed, #2563eb); display: flex; align-items: center; justify-content: center; font-size: 36px; margin: 0 auto 20px; box-shadow: 0 8px 32px rgba(124,58,237,0.5); }
  .quick-idle-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
  .quick-idle-desc { font-size: 13px; color: #6b7280; line-height: 1.6; margin-bottom: 20px; }
  .toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); padding: 12px 20px; border-radius: 14px; font-size: 13px; font-weight: 600; z-index: 999; white-space: nowrap; animation: slideUp 0.3s ease; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
  .toast-error { background: linear-gradient(135deg, #dc2626, #b91c1c); color: #fff; }
  @keyframes slideUp { from { opacity: 0; transform: translateX(-50%) translateY(16px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
  .success-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; min-height: 70vh; padding: 32px 16px; animation: fadeIn 0.4s ease; }
  .success-icon { width: 96px; height: 96px; border-radius: 28px; background: linear-gradient(135deg, #10b981, #059669); display: flex; align-items: center; justify-content: center; font-size: 44px; margin-bottom: 24px; box-shadow: 0 12px 40px rgba(16,185,129,0.5); animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
  @keyframes popIn { from { transform: scale(0.5); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  .success-title { font-size: 26px; font-weight: 800; margin-bottom: 10px; letter-spacing: -0.5px; }
  .success-sub { font-size: 14px; color: #6b7280; line-height: 1.6; margin-bottom: 8px; }
  .success-detail { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 16px 20px; margin: 20px 0 28px; width: 100%; text-align: left; }
  .success-detail-row { display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; }
  .success-detail-row span:first-child { color: #6b7280; }
  .success-detail-row span:last-child { font-weight: 600; }
  .divider { height: 1px; background: rgba(255,255,255,0.06); margin: 14px 0; }
`;

function App() {
  const [page, setPage] = useState('menu');
  const [room, setRoom] = useState('');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [topic, setTopic] = useState('');
  const [isBooked, setIsBooked] = useState(false);
  const [currentBooking, setCurrentBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scheduleSubmitted, setScheduleSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setDate(tomorrow.toISOString().split('T')[0]);
  }, []);

  WebApp.onEvent('viewportChanged', () => WebApp.expand());

  const showError = (msg) => {
    setSubmitError(msg);
    setTimeout(() => setSubmitError(''), 3000);
  };

  const handleQuickBook = async () => {
    if (!room) return showError('Please select a room');
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const bookingDate = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    const st = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
    const et = '23:59';
    const user = WebApp.initDataUnsafe?.user;
    setLoading(true);
    try {
      const data = await supabaseInsert({
        user_id: user?.id ?? 0,
        username: user?.username ?? null,
        full_name: user ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() : 'Unknown',
        booking_date: bookingDate,
        start_time: st,
        end_time: et,
        topic: 'Quick Book',
        room_id: room,
        status: 'approved',
      });
      setCurrentBooking({ id: data[0].id, date: bookingDate, start_time: st, end_time: et, topic: 'Quick Book', room });
      setIsBooked(true);
    } catch (e) {
      showError('Booking failed. Please try again.');
    }
    setLoading(false);
  };

  const handleRelease = async () => {
    if (!currentBooking) return;
    setLoading(true);
    try {
      await fetch(`${SUPABASE_URL}/rest/v1/bookings?id=eq.${currentBooking.id}`, {
        method: 'PATCH',
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'released' }),
      });
      setIsBooked(false);
      setCurrentBooking(null);
    } catch (e) {
      showError('Failed to release. Please try again.');
    }
    setLoading(false);
  };

  const handleScheduleBook = async () => {
    if (!room || !date || !startTime || !endTime || !topic) return showError('Please fill in all fields');
    if (startTime >= endTime) return showError('End time must be after start time');
    const user = WebApp.initDataUnsafe?.user;
    setLoading(true);
    try {
      await supabaseInsert({
        user_id: user?.id ?? 0,
        username: user?.username ?? null,
        full_name: user ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() : 'Unknown',
        booking_date: date,
        start_time: startTime,
        end_time: endTime,
        topic,
        room_id: room,
        status: 'pending',
      });
      setScheduleSubmitted(true);
    } catch (e) {
      showError('Failed to submit. Please try again.');
    }
    setLoading(false);
  };

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const dateStr = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
  const selectedRoomLabel = rooms.find(r => r.id === room)?.label ?? '';

  return (
    <>
      <style>{css}</style>
      <div className="app">

        {page === 'menu' && (
          <div className="page">
            <div className="header">
              <div className="header-icon">🏢</div>
              <div className="header-title">Conference Room</div>
              <div className="header-sub">{dateStr} · {timeStr}</div>
            </div>
            <div className="menu-grid">
              <div className="menu-card quick" onClick={() => setPage('quick')}>
                <div className="card-top">
                  <div className="card-emoji purple">⚡</div>
                  <div className="card-title">Quick Book</div>
                  <span className="card-badge badge-instant">INSTANT</span>
                </div>
                <div className="card-desc">Book the room right now · No approval needed · Release when done</div>
              </div>
              <div className="menu-card schedule" onClick={() => setPage('schedule')}>
                <div className="card-top">
                  <div className="card-emoji blue">📅</div>
                  <div className="card-title">Schedule Booking</div>
                  <span className="card-badge badge-approval">APPROVAL</span>
                </div>
                <div className="card-desc">Book for a future date & time · Admin reviews your request</div>
              </div>
            </div>
            <div className="info-footer">Use /mybookings in the bot to view all bookings</div>
          </div>
        )}

        {page === 'quick' && (
          <div className="page">
            {submitError && <div className="toast toast-error">❌ {submitError}</div>}
            <button className="back-btn" onClick={() => setPage('menu')}>← Back</button>
            {isBooked && currentBooking ? (
              <>
                <div className="booked-card">
                  <div className="booked-badge">🟢 Room Occupied</div>
                  <div className="booked-topic">{currentBooking.topic}</div>
                  <div className="booked-meta">
                    <span>🏢 {rooms.find(r => r.id === currentBooking.room)?.label}</span>
                    <span>📅 {currentBooking.date}</span>
                    <span>🕐 {currentBooking.start_time} – {currentBooking.end_time}</span>
                  </div>
                </div>
                <button className="btn btn-danger" onClick={handleRelease} disabled={loading}>
                  🔓 Release Room
                </button>
              </>
            ) : (
              <>
                <div className="section">
                  <div className="quick-idle">
                    <div className="quick-idle-icon">⚡</div>
                    <div className="quick-idle-title">Book Instantly</div>
                    <div className="quick-idle-desc">
                      Books the room from now until end of day.<br />
                      No approval needed — release when you're done.
                    </div>
                  </div>
                </div>
                <div className="section">
                  <div className="section-label">Select Room</div>
                  <div className="room-grid">
                    {rooms.map(r => (
                      <div key={r.id} className={`room-option ${room === r.id ? 'selected' : ''}`} onClick={() => setRoom(r.id)}>
                        <span className="room-option-emoji">{r.emoji}</span>
                        {r.label}
                      </div>
                    ))}
                  </div>
                </div>
                <button className="btn btn-primary" onClick={handleQuickBook} disabled={loading}>
                  {loading ? 'Booking...' : '⚡ Book Now'}
                </button>
              </>
            )}
          </div>
        )}

        {page === 'schedule' && (
          <div className="page">
            {submitError && <div className="toast toast-error">❌ {submitError}</div>}

            {scheduleSubmitted ? (
              <div className="success-screen">
                <div className="success-icon">✅</div>
                <div className="success-title">Request Submitted!</div>
                <div className="success-sub">
                  Your booking has been sent to the admin for approval.<br />
                  You'll be notified in Telegram once it's reviewed.
                </div>
                <div className="success-detail">
                  <div className="success-detail-row"><span>🏢 Room</span><span>{selectedRoomLabel}</span></div>
                  <div className="success-detail-row"><span>📅 Date</span><span>{date}</span></div>
                  <div className="success-detail-row"><span>🕐 Time</span><span>{startTime} – {endTime}</span></div>
                  <div className="success-detail-row"><span>📝 Topic</span><span>{topic}</span></div>
                </div>
                <button className="btn btn-primary" onClick={() => {
                  setScheduleSubmitted(false);
                  setRoom(''); setDate(''); setStartTime(''); setEndTime(''); setTopic('');
                  setPage('menu');
                }}>
                  Back to Home
                </button>
              </div>
            ) : (
              <>
                <button className="back-btn" onClick={() => setPage('menu')}>← Back</button>
                <div className="page-header">
                  <div className="page-title">📅 Schedule Booking</div>
                  <div className="page-sub">Submit a request for admin approval</div>
                </div>
                <div className="section">
                  <div className="section-label">Select Room</div>
                  <div className="room-grid">
                    {rooms.map(r => (
                      <div key={r.id} className={`room-option ${room === r.id ? 'selected' : ''}`} onClick={() => setRoom(r.id)}>
                        <span className="room-option-emoji">{r.emoji}</span>
                        {r.label}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="section">
                  <div className="section-label">Date</div>
                  <input type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} min={new Date().toISOString().split('T')[0]} />
                </div>
                <div className="section">
                  <div className="section-label">Start Time</div>
                  <div className="time-grid">
                    {timeSlots.map(t => (
                      <div key={t} className={`time-slot ${startTime === t ? 'selected' : ''}`} onClick={() => setStartTime(t)}>{t}</div>
                    ))}
                  </div>
                  <div className="divider" />
                  <div className="section-label">End Time</div>
                  <div className="time-grid">
                    {timeSlots.map(t => (
                      <div key={t} className={`time-slot ${endTime === t ? 'selected' : ''}`} onClick={() => setEndTime(t)}>{t}</div>
                    ))}
                  </div>
                </div>
                <div className="section">
                  <div className="section-label">Meeting Topic</div>
                  <input type="text" className="input" placeholder="e.g. Q4 Planning, Client Call..." value={topic} onChange={(e) => setTopic(e.target.value)} />
                </div>
                <button className="btn btn-schedule" onClick={handleScheduleBook} disabled={loading}>
                  {loading ? 'Submitting...' : '📅 Submit for Approval'}
                </button>
              </>
            )}
          </div>
        )}

      </div>
    </>
  );
}

export default App;
