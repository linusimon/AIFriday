import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AppRoutingModule } from './app-routing.module';

import { AppComponent } from './app.component';
import { LoginComponent } from './login/login.component';
import { AdminComponent } from './admin/admin.component';
import { AnalysisComponent } from './analysis/analysis.component';
import { ChatComponent } from './chat/chat.component';

import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';
import { TaskRoutingService } from './services/task-routing.service';
import { ChatService } from './services/chat.service';
import { AuthGuard } from './guards/auth.guard';
import { Nl2brPipe } from './pipes/nl2br.pipe';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    AdminComponent,
    AnalysisComponent,
    ChatComponent,
    Nl2brPipe
  ],
  imports: [
    BrowserModule,
    CommonModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule
  ],
  providers: [
    ApiService, 
    AuthService, 
    TaskRoutingService,
    ChatService,
    AuthGuard
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
