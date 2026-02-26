import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule, HttpClientModule, CommonModule],   
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  grafanaUrl: SafeResourceUrl;
  timer = '';
  timerStatus = '';
  pin = '';
  pinStatus = '';
  colorStatus = '';
  alarmOn = false;
  private apiBase = 'http://localhost:5001';

  constructor(private sanitizer: DomSanitizer, private http: HttpClient) { 
    const url = 'http://localhost:3000/d/iozgl79/smart-home?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s&kiosk';
    this.grafanaUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  ngOnInit() {
    setInterval(() => {
      this.http.get<any>(`${this.apiBase}/api/alarm/state`).subscribe({
        next: (res) => this.alarmOn = !!res.alarm_on,
        error: () => {}
      });
    }, 2000); 
  }

  sendPin() {
    const p = (this.pin || '').trim();
    if (!p) return;

    this.http.post<any>(`${this.apiBase}/api/dms/pin`, { pin: p }).subscribe({
      next: (res) => {
        this.pinStatus = res.pin_ok ? 'PIN OK ✅' : 'PIN BAD ❌';
        this.pin = '';
      },
      error: () => (this.pinStatus = 'Greška pri slanju PIN-a ❌'),
    });
  }

  setColor(color: string) {
    this.http.post<any>(`${this.apiBase}/api/brgb/color`, { color }).subscribe({
      next: () => (this.colorStatus = `BRGB -> ${color.toUpperCase()} ✅`),
      error: () => (this.colorStatus = `Greška BRGB ❌`),
    });
  }

  set4sd() {
    const raw = (this.timer || '').trim();
    if (!raw) {
      this.timerStatus = 'Unesi vreme ❗';
      return;
    }

    this.http.post<any>(`${this.apiBase}/api/4sd/set`, { value: raw }).subscribe({
      next: (res) => this.timerStatus = `4SD set ✅ (${res.value})`,
      error: (err) => this.timerStatus = err?.error?.hint ? `Greška ❌ (${err.error.hint})` : 'Greška ❌'
    });
  }

  set4sdNow() {
    this.http.post<any>(`${this.apiBase}/api/4sd/time`, {}).subscribe({
      next: () => this.timerStatus = '4SD -> current time ✅',
      error: () => this.timerStatus = 'Greška ❌'
    });
  }
}