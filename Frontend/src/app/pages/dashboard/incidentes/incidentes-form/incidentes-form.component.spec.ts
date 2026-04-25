import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IncidentesFormComponent } from './incidentes-form.component';

describe('IncidentesFormComponent', () => {
  let component: IncidentesFormComponent;
  let fixture: ComponentFixture<IncidentesFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IncidentesFormComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IncidentesFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
