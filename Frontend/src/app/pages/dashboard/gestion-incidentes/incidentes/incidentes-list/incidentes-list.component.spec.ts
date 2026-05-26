import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IncidentesListComponent } from './incidentes-list.component';

describe('IncidentesListComponent', () => {
  let component: IncidentesListComponent;
  let fixture: ComponentFixture<IncidentesListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IncidentesListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IncidentesListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
