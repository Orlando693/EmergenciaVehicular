import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SolicitudesDetailComponent } from './solicitudes-detail.component';

describe('SolicitudesDetailComponent', () => {
  let component: SolicitudesDetailComponent;
  let fixture: ComponentFixture<SolicitudesDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SolicitudesDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SolicitudesDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
