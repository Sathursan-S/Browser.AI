import { createRoot } from 'react-dom/client'

import Notification from './Notification'
import './Notification.css'

const container = document.getElementById('notification-root')
const root = createRoot(container!)

root.render(<Notification />)
