import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VehiculosFormComponent } from './vehiculos-form.component';

describe('VehiculosFormComponent', () => {
  let component: VehiculosFormComponent;
  let fixture: ComponentFixture<VehiculosFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VehiculosFormComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VehiculosFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
