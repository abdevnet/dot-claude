---
description: >-
  Fetch when generating, reviewing, or modifying Angular unit tests, component
  specs, service specs, or test mocks in .spec.ts files. Contains Swank-specific
  conventions for TestBed setup, moq.ts mocking, HttpTestingController,
  signal testing with fakeAsync, test data factories, and test organization.
---

# Angular Unit Testing Standards

## Component Test Setup

Use `ComponentFixture` and `TestBed.configureTestingModule` for component tests. Add the component under test to the `imports` array (not `declarations`). Include `BrowserAnimationsModule` when the component uses Angular Material. Use `provideHttpClient()` and `provideHttpClientTesting()` when the component or its dependencies make HTTP calls. Use `provideRouter([])` when the component uses routing.

```typescript
describe('FilmListComponent', () => {
  let component: FilmListComponent;
  let fixture: ComponentFixture<FilmListComponent>;
  let filmServiceMock: Mock<FilmService>;

  beforeEach(waitForAsync(() => {
    filmServiceMock = new Mock<FilmService>();
    filmServiceMock.setup(x => x.getFilms()).returns(of([]));

    TestBed.configureTestingModule({
      imports: [FilmListComponent, BrowserAnimationsModule],
      providers: [
        { provide: FilmService, useValue: filmServiceMock.object() },
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FilmListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

### Deferred Component Creation

When the component's behavior depends on mock setup that varies per test, separate `TestBed` configuration from component creation. Define a `createComponent` helper and call it inside each test after arranging mocks.

```typescript
beforeEach(async () => {
  importServiceMock = new Mock<ImportService>();
  importServiceMock.setup(x => x.importAssets(It.IsAny())).returns(of([]));

  await TestBed.configureTestingModule({
    imports: [ImportResultDialogComponent],
    providers: [
      { provide: ImportService, useValue: importServiceMock.object() },
      { provide: MatDialogRef, useValue: dialogRefMock.object() },
      { provide: MAT_DIALOG_DATA, useValue: mockDialogData },
      provideRouter([]),
    ],
  }).compileComponents();
});

const createComponent = () => {
  fixture = TestBed.createComponent(ImportResultDialogComponent);
  component = fixture.componentInstance;
};

it('should populate results on success', () => {
  importServiceMock.setup(x => x.importAssets(It.IsAny())).returns(of(mockResults));

  createComponent();
  fixture.detectChanges();

  expect(component['resultsToDisplay']()).toEqual(mockResults);
});
```

## Service Test Setup

Use `TestBed.configureTestingModule` with the service under test resolved via `TestBed.inject`. Provide mocked dependencies in the `providers` array.

```typescript
describe('AssetsService', () => {
  let service: AssetsService;
  let mockToastrService: Mock<ToastrService>;
  let mockHttpClient: Mock<HttpClient>;

  beforeEach(() => {
    mockToastrService = new Mock<ToastrService>();
    mockToastrService.setup(x => x.error(It.IsAny(), It.IsAny())).returns();
    mockToastrService.setup(x => x.success(It.IsAny(), It.IsAny())).returns();

    mockHttpClient = new Mock<HttpClient>();

    TestBed.configureTestingModule({
      providers: [
        AssetsService,
        { provide: ToastrService, useValue: mockToastrService.object() },
        { provide: HttpClient, useValue: mockHttpClient.object() },
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(AssetsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
```

## HTTP Service Testing with HttpTestingController

When testing services that call `HttpClient` directly, use `provideHttpClient(withInterceptorsFromDi())` and `provideHttpClientTesting()` with `HttpTestingController`. Call `httpMock.verify()` in `afterEach`.

```typescript
describe('ProductsService', () => {
  let service: ProductsService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(ProductsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should return products', () => {
    const mockProducts = [{ id: 1, name: 'Test' }];

    service.getProducts().subscribe(products => {
      expect(products.length).toBe(1);
      expect(products[0].name).toBe('Test');
    });

    const request = httpMock.expectOne({ method: 'GET' });
    expect(request.request.url).toMatch('api/products');
    request.flush(mockProducts);
  });

  it('should handle HTTP errors', () => {
    service.getProducts().subscribe({
      next: () => fail('expected error'),
      error: (err: HttpErrorResponse) => {
        expect(err.error).toBe('server error');
      },
    });

    const request = httpMock.expectOne({ method: 'GET' });
    request.flush('server error', { status: 500, statusText: 'Internal Server Error' });
  });
});
```

## Mocking with moq.ts

- Use `new Mock<T>()` to create type-safe mocks.
- Use `.setup(x => x.method()).returns(value)` to configure return values.
- Use `.object()` to get the mock instance for provider registration.
- Use `It.IsAny<T>()` for argument matching when the exact value is not relevant.
- Use `.verify()` with `Times` to assert calls were made.
- Do not use Jasmine `spyOn` for service dependencies. Reserve `spyOn` for spying on the component under test's own methods when needed.

```typescript
// Setup
filmServiceMock = new Mock<FilmService>();
filmServiceMock.setup(x => x.getFilms()).returns(of(mockFilms));
filmServiceMock.setup(x => x.getFilmById(1)).returns(of(mockFilm));

// Verification
filmServiceMock.verify(
  x => x.importAssets(mockFilesToImport),
  Times.Once()
);

// Argument matching
importServiceMock.verify(
  x => x.importAssets(
    It.Is<FileToImport[]>(items =>
      items.length === 2 &&
      items[0].name === 'video1.ts'
    )
  ),
  Times.Once()
);
```

### Jasmine spyOn

Use `spyOn` only to spy on the component under test's own methods when you need to verify internal call chains.

```typescript
const retrySpy = spyOn<any>(component, 'retryImport').and.callThrough();

await component['overrideInexactDuplicateInRequest'](mockResults[1], true);

expect(retrySpy).toHaveBeenCalledTimes(1);
const callArgs = retrySpy.calls.mostRecent().args[0];
expect(callArgs).toContain(mockResults[0]);
```

## Signal-Based Components

Use `fakeAsync` and `tick()` to ensure signal updates propagate before assertions.

```typescript
it('should update filtered films when filter changes', fakeAsync(() => {
  component.searchFilter.set('action');
  fixture.detectChanges();
  tick();

  expect(component.filteredFilms().length).toBe(2);
}));
```

## httpResource Testing

Use `HttpTestingController` to intercept and flush HTTP requests made by `httpResource`.

```typescript
it('should load films via httpResource', fakeAsync(() => {
  fixture.detectChanges();
  tick();

  const request = httpMock.expectOne('api/films');
  request.flush(mockFilms);
  tick();

  expect(component.films()).toEqual(mockFilms);
}));
```

## Accessing Private and Protected Members

Use bracket notation to access `private` and `protected` members in tests.

```typescript
// Reading a private signal
expect(component['resultsToDisplay']()).toEqual(mockResults);

// Calling a protected method
await component['retryImport']([mockResults[0]]);

// Writing to a private signal
component['resultsToDisplay'].set(mockResults);
```

## Test Data Factories

Define `createMock*` factory functions with partial overrides at the top of the `describe` block. Use these to build test data consistently across tests.

```typescript
const createMockFilm = (overrides?: Partial<Film>): Film => ({
  id: 1,
  title: 'Test Film',
  studioName: 'Test Studio',
  releaseYear: 2024,
  isActive: true,
  ...overrides,
});

const createMockImportResult = (overrides?: Partial<ImportResult>): ImportResult => ({
  directoryPath: '//test/path',
  filename: 'test-file.ts',
  outcome: ImportOutcome.Success,
  message: 'Import successful',
  hasRollbackError: false,
  ...overrides,
});
```

Use a second factory that derives from another model when test data is related.

```typescript
const createMockImportResultForFile = (
  file: FileToImport,
  overrides?: Partial<ImportResult>
): ImportResult =>
  createMockImportResult({
    filename: file.name,
    directoryPath: file.directoryPath,
    ...overrides,
  });
```

## Test Organization

Structure test files with `describe` blocks that group tests by method, feature, or computed signal.

```typescript
describe('ImportResultDialogComponent', () => {
  // shared setup

  describe('ngOnInit', () => {
    it('should call importService with the provided files', () => { /* ... */ });
    it('should populate results on success', () => { /* ... */ });
    it('should set errorDisplay on failure', () => { /* ... */ });
  });

  describe('computed signals', () => {
    describe('importSuccessCount and importFailCount', () => {
      it('should calculate correctly with all successes', () => { /* ... */ });
      it('should calculate correctly with mixed results', () => { /* ... */ });
    });

    describe('sortedResults', () => {
      it('should sort successes to the bottom', () => { /* ... */ });
    });
  });

  describe('retryImport', () => {
    it('should apply validationOverrides to items', async () => { /* ... */ });
    it('should update resultsToDisplay on success', async () => { /* ... */ });
    it('should restore original status on failure', async () => { /* ... */ });
  });
});
```

## Test Composition

Use `// ARRANGE`, `// ACT`, and `// ASSERT` comments within each test.
