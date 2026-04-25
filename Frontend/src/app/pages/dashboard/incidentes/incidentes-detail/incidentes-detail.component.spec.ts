import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IncidentesDetailComponent } from './incidentes-detail.component';

describe('IncidentesDetailComponent', () => {
  let component: IncidentesDetailComponent;
  let fixture: ComponentFixture<IncidentesDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IncidentesDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IncidentesDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
