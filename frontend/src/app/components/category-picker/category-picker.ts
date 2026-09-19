import { Component, Input, Output, EventEmitter, OnInit, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CategoryService, Category } from '../../services/category';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';

@Component({
  selector: 'app-category-picker',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './category-picker.html',
  styleUrls: ['./category-picker.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CategoryPicker),
      multi: true
    }
  ]
})
export class CategoryPicker implements OnInit, ControlValueAccessor {
  @Input() kindFilter?: 'income' | 'expense';
  categories: Category[] = [];
  filteredCategories: Category[] = [];

  value: string | null = null;
  onChange = (v: any) => {};
  onTouched = () => {};

  constructor(private categoryService: CategoryService) {}

  ngOnInit() {
    this.categoryService.listCategories().subscribe(data => {
      this.categories = data;
      this.filterCategories();
    });
  }

  ngOnChanges() {
    this.filterCategories();
  }

  filterCategories() {
    if (this.kindFilter) {
      this.filteredCategories = this.categories.filter(c => c.kind === this.kindFilter && !c.archived);
    } else {
      this.filteredCategories = this.categories.filter(c => !c.archived);
    }
  }

  writeValue(val: any): void {
    this.value = val;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    // optional
  }

  onSelectChange(event: Event) {
    const val = (event.target as HTMLSelectElement).value;
    this.value = val;
    this.onChange(this.value);
    this.onTouched();
  }
}
