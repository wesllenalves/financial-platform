import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { AuthService } from '../auth/auth';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './shell.html',
  styleUrls: ['./shell.scss']
})
export class Shell {
  constructor(private authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}
