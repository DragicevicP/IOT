import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  grafanaUrl: SafeResourceUrl;

  constructor(private sanitizer: DomSanitizer) {
    
    const url = 'http://localhost:3000/d/iozgl79/smart-home?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s&kiosk';

    this.grafanaUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }
}