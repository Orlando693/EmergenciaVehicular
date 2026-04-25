import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ServiciosListComponent } from './servicios-list.component';

describe('ServiciosListComponent', () => {
  let component: ServiciosListComponent;
  let fixture: ComponentFixture<ServiciosListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ServiciosListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ServiciosListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
