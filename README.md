# 💬 napishi_sashke

**Терминальный мессенджер с end-to-end шифрованием**

Красивый чат прямо в терминале. Сообщения шифруются, можно отправлять голосовые и картинки

---

<table>
<tr>
<td width="280" valign="top">
  <img src="https://github.com/user-attachments/assets/d4c0f837-e5cb-45fd-8b21-aa24de5891b9" width="260">
</td>
<td valign="top">

### ✨ Возможности

- 🔐 End-to-end шифрование  
- 🎤 Голосовые сообщения  
- 🖼 Отправка и просмотр изображений  
- 🎨 Красивый интерфейс  
- ⚡ Работает через WebSocket  

</td>
</tr>
</table>

### 🛠 Стек

**Клиент**
- Python + `websockets`, `cryptography`, `rich`, `prompt-toolkit`, `pillow`

**Сервер**
- FastAPI + WebSocket + SQLAlchemy

---

### 🚀 Быстрый старт

```bash
# Клонируем
git clone https://github.com/alekstarat/napishi_sashke.git
cd napishi_sashke

# Сервер
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload

# Клиент (в другом терминале)
cd client
pip install -r requirements.txt
python main.py
