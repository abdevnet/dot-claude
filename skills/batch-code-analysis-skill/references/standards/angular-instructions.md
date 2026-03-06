# AI Angular Instructions for {Application Name}

## Project Overview
{Application Description}

## Angular Framework Guidelines

### Modern Angular Patterns (v20+)
- **Standalone Components**: Use `imports` array instead of NgModules
- **Signals**: Prefer `signal()`, `computed()`, and `effect()` for reactive state
- **New Control Flow**: Use `@if`, `@for`, `@switch` instead of `*ngIf`, `*ngFor`, `*ngSwitch`
- **Input/Output**: Use `input<T>()`, `model<T>()`, and `output<T>()` functions
- **Change Detection**: Implement `OnPush` strategy with signals for optimal performance
- **Dependency Injection**: Use `inject()` function instead of constructor injection

### Angular Signals Best Practices
```typescript
// State management with signals
public loading = signal(false);
public data = signal<MyData[]>([]);
public selectedId = signal<number | null>(null);

// Computed values
public filteredData = computed(() => 
  this.data().filter(item => item.active)
);

// Effects for side effects
private dataEffect() {
  effect(() => {
    if (this.selectedId()) {
      this.loadDetails(this.selectedId()!);
    }
  });
}
```

## Angular Material Guidelines

### Material Design Components
- **Navigation**: Use `mat-toolbar`, `mat-sidenav`, `mat-nav-list`
- **Layout**: Use `mat-card`, `mat-expansion-panel`, `mat-grid-list`
- **Forms**: Use `mat-form-field`, `mat-input`, `mat-select`, `mat-checkbox`
- **Data Display**: Use `mat-table`, `mat-paginator`, `mat-sort`
- **Feedback**: Use `mat-progress-bar`, `mat-spinner`, `mat-snack-bar`
- **Buttons**: Use `matButton="outlined"`, `matButton="elevated"`, `matFab`, `matIconButton`

### Form Field Patterns
```typescript
// Standard form field with validation
<mat-form-field appearance="outline" subscriptSizing="dynamic">
  <mat-label>Name</mat-label>
  <input matInput [formControl]="nameControl" required>
  <mat-error>Name is required</mat-error>
  <mat-hint>Enter your full name</mat-hint>
</mat-form-field>

// Select with options
<mat-form-field appearance="outline">
  <mat-label>Category</mat-label>
  <mat-select [formControl]="categoryControl">
    @for (option of options(); track option.id) {
      <mat-option [value]="option.id">{{ option.name }}</mat-option>
    }
  </mat-select>
</mat-form-field>
```

### Data Tables with Material
```typescript
// Use MatTableDataSource with sorting and pagination
public dataSource = new MatTableDataSource<MyData>();
public displayedColumns = signal(['name', 'status', 'date', 'actions']);

// Configure table features
ngAfterViewInit() {
  this.dataSource.sort = this.sort;
  this.dataSource.paginator = this.paginator;
  this.dataSource.filterPredicate = this.customFilterPredicate;
}
```

### Material Theming and Styling
```typescript
// Use Angular Material's theming system
@use '@angular/material' as mat;

// Apply theme-aware colors
.my-component {
  background-color: mat.m2-get-color-from-palette(mat.$m2-grey-palette, 50);
  color: mat.m2-get-color-from-palette(mat.$m2-grey-palette, 900);
}

// Use Material Design spacing
.content {
  padding: 16px; // Use 8px increments
  margin: 8px 16px;
}
```

### TypeScript Aliases
Always use path aliases from tsconfig.json:
- `@models/` for model imports
- `@services/` for service imports  
- `@material` for Angular Material imports
- `@components/` for shared components
- `@state/` for NGXS state management

### Component Structure
Follow this component organization:
```typescript
export class MyComponent {
  // == DEPENDENCIES ============================

  private readonly service = inject(MyService);

  // == INPUTS & OUTPUTS ========================

  public data = input<MyType>();
  public searchFilter = model<string>('');

  // == STATE ===================================

  public selectedItem = signal<MyType | null>(null);
  public filteredData = computed(() => { /* logic */ });

  // == LIFE CYCLE ==============================

  constructor() {}

  ngOnInit(): void { }

  // == METHODS =================================

  public handleClick(): void { /* logic */ }
  private _helperMethod(): void { /* logic */ }
}
```

## Testing Guidelines

### Angular Testing Patterns
- **Component Testing**: Use `ComponentFixture` and `TestBed.configureTestingModule`
- **Service Mocking**: Use `Mock<T>` from moq.ts library for type-safe mocking
- **HTTP Testing**: Use `HttpTestingController` for httpResource components
- **Async Testing**: Use `fakeAsync` and `tick()` for signal-based components
- **Router Mocking**: Mock `ActivatedRoute` with proper paramMap observables

### Testing Setup Examples
```typescript
// Component test setup with signals
describe('MyComponent', () => {
  let component: MyComponent;
  let fixture: ComponentFixture<MyComponent>;
  let serviceMock: Mock<MyService>;

  beforeEach(waitForAsync(() => {
    serviceMock = new Mock<MyService>();
    
    TestBed.configureTestingModule({
      imports: [BrowserAnimationsModule],
      providers: [
        { provide: MyService, useValue: serviceMock.object() },
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();
  }));

  beforeEach(fakeAsync(() => {
    serviceMock.setup(x => x.getData()).returns(of(mockData));
    
    fixture = TestBed.createComponent(MyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    tick(); // Process signal updates
  }));
});
```

### HTTP Resource Testing
```typescript
// For components using httpResource
it('should load data via httpResource', fakeAsync(() => {
  fixture.detectChanges();
  tick();
  
  const req = httpMock.expectOne('api/data');
  req.flush(mockData);
  tick();
  
  expect(component.data()).toEqual(mockData);
}));
```

## File Naming
- Components: `my-component.component.ts`
- Services: `my-service.service.ts`  
- Models: `my-model.ts`
- Spec files: `my-file.spec.ts`

## Performance & Best Practices

### Performance Optimization
- **OnPush Strategy**: Use with signals for optimal change detection
- **TrackBy Functions**: Always provide trackBy for `@for` loops with dynamic data
- **Lazy Loading**: Use route-based code splitting for large modules
- **Virtual Scrolling**: Use `cdk-virtual-scroll-viewport` for large lists

## Do Not Use
- `*ngFor`, `*ngIf` - use new control flow syntax instead
- Relative imports - always use path aliases
- `{ static: true }` in ViewChild unless accessing in ngOnInit
- Old RxJS patterns - use modern operators and factory functions
- Constructor injection - use `inject()` function instead
- `any` type - prefer proper TypeScript typing
