---
description: >-
  Fetch when generating, reviewing, or modifying Angular components, services,
  templates, styles, state services, or route configuration in .ts, .html,
  or .scss files. Contains Swank-specific conventions for standalone components,
  signal-based reactivity and state management, control flow syntax, Angular
  Material, component organization, and file naming.
---

# Angular Coding Standards

## Standalone Components

- Use standalone components with the `imports` array. Do not use NgModules.
- Use the `inject()` function for dependency injection. Do not use constructor injection.

```typescript
// Do
export class FilmListComponent {
  private readonly filmService = inject(FilmService);
}

// Do not
export class FilmListComponent {
  constructor(private readonly filmService: FilmService) {}
}
```

## Signals and Reactivity

- Use `signal()`, `computed()`, and `effect()` for reactive state.
- Do not use `BehaviorSubject`, `Observable` properties, or manual `subscribe()` calls where signals are sufficient.

```typescript
// Do
public readonly loading = signal(false);
public readonly films = signal<Film[]>([]);
public readonly selectedId = signal<number | null>(null);

public readonly activeFilms = computed(() =>
  this.films().filter(film => film.active)
);

constructor(){
  this._handleSelection();
}

private _handleSelection(): void {
  effect(() => {
    if (this.selectedId()) {
      this.loadDetails(this.selectedId()!);
    }
  });
}

// Do not
public readonly loading$ = new BehaviorSubject<boolean>(false);
public readonly films$ = new BehaviorSubject<Film[]>([]);

public readonly activeFilms$ = this.films$.pipe(
  map(films => films.filter(film => film.active))
);

ngOnInit(): void {
  this.selectedId$.pipe(
    filter(id => id !== null),
    switchMap(id => this.loadDetails(id))
  ).subscribe();
}
```

### Bridging Signals and RxJS

Use `toSignal()` to convert Observables into signals. Use `toObservable()` to convert signals into Observables when RxJS operators are needed.

```typescript
// Do: Convert an Observable to a signal
private _languages = toSignal<Language[]>(this.languagesService.getLanguages());

// Do: Convert route query params to a signal
private queryParams = toSignal(this.activatedRoute.queryParams, { initialValue: {} });

// Do: Convert a signal to an Observable for debounce, switchMap, etc.
private filter$ = toObservable(this.filterState.filter);
```

### Subscriptions

- Use object notation when calling `subscribe()`.
- Include only the handlers you need (`next`, `error`, `complete`).
- Keep handler bodies focused on side effects.

```typescript
this.getUser().subscribe({
  next: (user: User) => {
    ...
  },
  error: (error) => {
    ...
  }
});
```

### Subscription Cleanup

- Use `takeUntilDestroyed()` for subscription cleanup.
- Inject `DestroyRef` and provide it only for subscriptions outside of injection context.
- Do not use `takeUntilDestroyed()` for subscriptions that complete automatically.
    - e.g. `MatDialog.afterClosed()`, `HttpClient` methods, and services that pass through to `HttpClient` methods.
- Do not implement `OnDestroy` solely to unsubscribe.

```typescript
// Do
private readonly destroyRef = inject(DestroyRef);
private readonly userService = inject(UserService);
private readonly username = signal<string>('');
private readonly liveData = signal<string[]>([]);

constructor(){
  // userService.getUser() is a method that only calls HttpClient.get()
  this.userService.getUser().subscribe((name) => this.username.set(name))
  this.getLiveData().pipe(
    takeUntilDestroyed()
  )
  .subscribe({next: (data: string[]) => this.liveData.set(data)});
}

ngAfterViewInit(): void {
  fromEvent(window, 'resize')
    .pipe(
      debounceTime(100),
      tap(() => this.handleResize()),
      takeUntilDestroyed(this.destroyRef),
    )
    .subscribe();
}

// Do not
private subscription = new Subscription();

ngAfterViewInit(): void {
  this.subscription.add(
    fromEvent(window, 'resize').pipe(debounceTime(100)).subscribe()
  );
}

ngOnDestroy(): void {
  this.subscription.unsubscribe();
}
```

## Control Flow

- Use `@if`, `@for`, and `@switch` block syntax.
- Do not use `*ngIf`, `*ngFor`, or `*ngSwitch` structural directives.
- Always provide a `track` expression for `@for` loops with dynamic data.

```html
<!-- Do -->
@if (loading()) {
  <mat-spinner />
} @else {
  @for (film of films(); track film.id) {
    <app-film-card [film]="film" />
  }
}

<!-- Do not -->
<mat-spinner *ngIf="loading"></mat-spinner>
<app-film-card *ngFor="let film of films" [film]="film"></app-film-card>
```

## Inputs, Outputs, and Models

- Use `input<T>()`, `output<T>()`, and `model<T>()` functions.
- Do not use `@Input()` and `@Output()` decorators.

```typescript
// Do
public film = input<Film>();
public searchFilter = model<string>('');
public selected = output<Film>();

// Do not
@Input() film: Film;
@Output() selected = new EventEmitter<Film>();
```

## Change Detection

- Use `OnPush` change detection strategy on all components.

```typescript
// Do
@Component({
  selector: 'app-film-list',
  templateUrl: './film-list.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FilmListComponent {}

// Do not
@Component({
  selector: 'app-film-list',
  templateUrl: './film-list.component.html'
})
export class FilmListComponent {}
```

## Access Modifiers

- Use `protected` on members consumed by the template but not by external consumers.
- Use `private` on members that are purely internal.
- Use `public` on members that are part of the component or service's public API.
- Use `readonly` on injected dependencies.

```typescript
// Do
export class FilmListComponent {
  private readonly filmService = inject(FilmService);

  protected readonly loading = signal(false);
  protected readonly films = signal<Film[]>([]);

  public readonly selectedFilm = input<Film>();

  private loadFilms(): void { /* ... */ }
}

// Do not: everything public by default
export class FilmListComponent {
  filmService = inject(FilmService);
  loading = signal(false);
  loadFilms(): void { /* ... */ }
}
```

## Mutability
- Use `readonly` on members that should not be re-assigned. (Including signals and most FormControls)
- Use `const` for local variables that should not have their value changed.

```typescript
protected readonly mySignal = signal<number>(0);
protected readonly myComputed = computed<number>(() => this.mySignal() * 2);

protected increment(): void {
  const originalTotal = this.myComputed();
  let currentValue = this.mySignal();
  currentValue += 1;
  this.mySignal.set(currentValue);
  console.log(`${originalTotal} -> ${this.myComputed()}`);
}
```

## Component Organization

Follow this ordering within a component class. Use `// == SECTION NAME ==` comments to separate each section. Not every section applies to every component. Only include sections that the component uses.

```typescript
export class FilmListComponent implements OnInit {
  // == DEPENDENCIES ============================
  private readonly filmService = inject(FilmService);
  private readonly destroyRef = inject(DestroyRef);

  // == VIEW CHILDREN ===========================
  @ViewChild(MatSort) sort!: MatSort;

  // == INPUTS & OUTPUTS ========================
  public readonly studioId = input<number>();
  public readonly searchFilter = model<string>('');

  // == STATE ===================================
  protected readonly selectedFilm = signal<Film | null>(null);
  protected readonly filteredFilms = computed(() => { /* ... */ });

  // == LIFE CYCLE ==============================
  constructor() {
    this._selectionEffect();
  }

  ngOnInit(): void {
    this.selectedFilm.set(this.filmService.defaultFilm())
  }

  // == EFFECTS =================================
  private _selectionEffect(): void {
    effect(() => { /* ... */ });
  }

  // == ACTIONS =================================
  protected handleSelect(): void { /* ... */ }

  // == HELPERS =================================
  private loadDetails(): void { /* ... */ }
}
```

## Signal-Based State Services

Use injectable services with signals for state management. Expose state as readonly signals with explicit setter methods. Do not expose writable signals directly.

```typescript
@Injectable({ providedIn: 'root' })
export class FilmFilterState {
  // == DEPENDENCIES ============================
  private readonly router = inject(Router);

  // == STATE ===================================
  private readonly _searchText = signal<string>('');
  private readonly _selectedGenre = signal<string | null>(null);
  private readonly _loading = signal<boolean>(false);

  public readonly searchText = this._searchText.asReadonly();
  public readonly selectedGenre = this._selectedGenre.asReadonly();
  public readonly loading = this._loading.asReadonly();

  public setSearchText(text: string) {
    this._searchText.set(text);
  }

  public setSelectedGenre(genre: string | null) {
    this._selectedGenre.set(genre);
  }

  public setLoading(isLoading: boolean) {
    this._loading.set(isLoading);
  }

  // == DERIVED STATE ===========================
  public readonly filter = computed<FilmFilter>(() => {
    return {
      search: this.searchText(),
      genre: this.selectedGenre(),
    };
  });

  // == LIFE CYCLE ==============================
  constructor() {
    this._updateQueryString();
  }

  // == SIDE EFFECTS ============================
  private _updateQueryString(): void {
    effect(() => {
      const queryString = this._buildQueryString();
      this.router.navigate([], { queryParams: queryString });
    });
  }
}
```

### State Service Organization

Follow this ordering within a state service. Only include sections that apply.

| Section | Contents |
|---|---|
| `DEPENDENCIES` | Injected services and other state services |
| `CONSTANTS` | Static readonly values |
| `STATE` | Private writable signals, public readonly exposures, and setter methods |
| `DERIVED STATE` | `computed()` signals |
| `SIDE EFFECTS` | `effect()` calls |
| `ACTIONS` | Methods that coordinate API calls, state updates, and loading indicators |

### Consuming State in Templates

Components inject state services as `protected` and read signals directly in the template.

```typescript
// Component class
export class FilmFilterBarComponent {
  protected readonly filterState = inject(FilmFilterState);
}
```

```html
<!-- Template -->
<input matInput [value]="filterState.searchText()" />
<mat-checkbox
  [checked]="filterState.includeArchived()"
  (change)="filterState.setIncludeArchived($event.checked)">
  Include Archived
</mat-checkbox>
```

## Enums

Use string enums. Document each member with a JSDoc comment when the meaning is not obvious from the name.

```typescript
/** The possible outcomes of an import operation. */
export enum ImportOutcome {
  /** The asset was successfully imported. */
  Success = 'Success',

  /** There was an error during import. */
  Error = 'Error',

  /** The asset was already imported. */
  AlreadyImported = 'AlreadyImported',
}
```

## Models

Use interfaces for data transfer objects and API response shapes. Use classes only when behavior (methods, decorators) is required.

```typescript
// Do: interface for a data shape
export interface Film {
  id: number;
  title: string;
  studioName: string;
  releaseYear: number;
}

// Do: class when behavior is needed
export class DmpDevice {
  @Searchable
  customerNumber: number;

  @Searchable
  serial: string;

  deployedMediaPlayerId: number;
}
```

## Path Aliases

Always use tsconfig path aliases for imports. Do not use relative imports.

| Alias | Use For |
|---|---|
| `@models/` or `@models` | Model imports |
| `@services/` or `@services` | Service imports |
| `@material` | Angular Material barrel imports |
| `@components/` | Shared component imports |
| `@state/` | State service imports |
| `@shared/` | Shared utilities, directives, validators |

```typescript
// Do
import { Film } from '@models/film';
import { FilmService } from '@services/film.service';
import { FilmFilterState } from '@state/film-filter/film-filter.state';

// Do not
import { Film } from '../../models/film';
import { FilmService } from '../../../services/film.service';
```

## TypeScript

- Never use the `any` type. Use proper TypeScript typing.

```typescript
// Do
public handleResponse(data: unknown): void {
  const film = data as Film;
}

public parseItems<T>(items: T[]): T[] {
  return items.filter(item => item !== null);
}

// Do not
public handleResponse(data: any): void { }
public parseItems(items: any[]): any[] { }
```

## Angular Material

### Form Fields

Use `appearance="outline"` and `subscriptSizing="dynamic"` as defaults.

```html
<mat-form-field appearance="outline" subscriptSizing="dynamic">
  <mat-label>Name</mat-label>
  <input matInput [formControl]="nameControl" required>
  <mat-error>Name is required</mat-error>
  <mat-hint>Enter your full name</mat-hint>
</mat-form-field>

<mat-form-field appearance="outline">
  <mat-label>Category</mat-label>
  <mat-select [formControl]="categoryControl">
    @for (option of options(); track option.id) {
      <mat-option [value]="option.id">{{ option.name }}</mat-option>
    }
  </mat-select>
</mat-form-field>
```

### Data Tables

Use `MatTableDataSource` with sorting and pagination.

```typescript
public dataSource = new MatTableDataSource<Film>();
public readonly displayedColumns = signal(['title', 'studio', 'releaseDate', 'actions']);

ngAfterViewInit(): void {
  this.dataSource.sort = this.sort;
  this.dataSource.paginator = this.paginator;
  this.dataSource.filterPredicate = this.customFilterPredicate;
}
```

### Theming and Styling

Use Angular Material's theming system for theme-aware colors. Use 8px increments for spacing.

```scss
@use '@angular/material' as mat;

.my-component {
  background-color: mat.m2-get-color-from-palette(mat.$m2-grey-palette, 50);
  color: mat.m2-get-color-from-palette(mat.$m2-grey-palette, 900);
}

.content {
  padding: 16px;
  margin: 8px 16px;
}
```

## Performance

- Use route-based lazy loading for code splitting. Use `loadComponent` for single components and `loadChildren` for route groups.

```typescript
// Do: lazy-load a single component
export const routes: Routes = [
  {
    path: 'films',
    loadComponent: () => import('./films/film-list.component')
      .then(m => m.FilmListComponent)
  }
];

// Do: lazy-load a route group
export const routes: Routes = [
  {
    path: 'transcodes',
    loadChildren: () => import('./transcodes/transcodes.routes')
      .then(r => r.TRANSCODE_ROUTES)
  }
];

// Do not: eager import
export const routes: Routes = [
  { path: 'films', component: FilmListComponent }
];
```

- Use `cdk-virtual-scroll-viewport` for large lists (hundreds of items or more).

```html
<cdk-virtual-scroll-viewport itemSize="48" class="list-viewport">
  @for (film of films(); track film.id) {
    <app-film-card [film]="film" />
  }
</cdk-virtual-scroll-viewport>
```

- Do not use `{ static: true }` in `ViewChild` unless the element is needed in `ngOnInit` and is not inside a conditional template.

```typescript
// Do: default static: false
@ViewChild(MatSort) sort!: MatSort;

// Do not: unless you specifically need access in ngOnInit
@ViewChild(MatSort, { static: true }) sort!: MatSort;
```

## File Naming

| File Type | Convention | Example |
|---|---|---|
| Component | `name.component.ts` | `film-list.component.ts` |
| Service | `name.service.ts` | `film.service.ts` |
| State service | `name.state.ts` | `film-filter.state.ts` |
| Model | `name.ts` | `film.ts` |
| Enum | `name.enum.ts` | `import-outcome.enum.ts` |
| Test | `name.spec.ts` | `film-list.component.spec.ts` |
| Route file | `name.routes.ts` | `transcodes.routes.ts` |
