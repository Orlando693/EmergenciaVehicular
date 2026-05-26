import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VehiculosListComponent } from './vehiculos-list.component';

describe('VehiculosListComponent', () => {
  let component: VehiculosListComponent;
  let fixture: ComponentFixture<VehiculosListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VehiculosListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VehiculosListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
