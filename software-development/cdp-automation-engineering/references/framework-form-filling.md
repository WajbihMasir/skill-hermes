# Framework-Aware Form Filling

## The Problem: Controlled Components

Modern frameworks (React, Vue, Svelte) use controlled components — the framework owns the input state, not the DOM. Direct DOM manipulation is silently reverted.

```javascript
// This does NOT work with React/Vue:
input.value = 'hello';
// Framework re-renders and resets to its internal state
```

## The Solution: Native Value Setters

Bypass the framework's setter by calling the native prototype method directly:

```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
).set;
nativeSetter.call(input, 'hello');
```

This updates the DOM value AND triggers the framework's change detection when combined with proper events.

## Required Events

Different frameworks listen to different events:

| Framework | Required Events |
|-----------|----------------|
| React | `input` (bubbles) |
| Vue | `input` + `change` (bubbles) |
| Svelte | `input` + `change` + `blur` |
| Angular | `input` + `change` |

Always dispatch all three to be safe:

```javascript
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
```

## Textarea Support

For `<textarea>` elements, use the textarea prototype:

```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
).set;
```

## Select Dropdowns

For `<select>` elements, set value and dispatch change:

```javascript
select.value = 'option_value';
select.dispatchEvent(new Event('change', { bubbles: true }));
```

## Debugging Tips

1. **Check if value stuck:** After setting, read `input.value` back — if empty, the setter didn't work
2. **Check for validation errors:** Look for `[class*=error]`, `[role=alert]` after blur
3. **Check network tab:** If submit doesn't navigate, the API returned an error — capture it with NetworkMonitor
4. **Wait for framework mount:** If setting value too early (before React mounts), it won't stick — add a small delay or wait for a specific element
