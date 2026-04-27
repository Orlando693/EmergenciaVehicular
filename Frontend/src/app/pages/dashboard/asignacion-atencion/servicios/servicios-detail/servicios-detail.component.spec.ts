import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ServiciosDetailComponent } from './servicios-detail.component';

describe('ServiciosDetailComponent', () => {
  let component: ServiciosDetailComponent;
  let fixture: ComponentFixture<ServiciosDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ServiciosDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ServiciosDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
