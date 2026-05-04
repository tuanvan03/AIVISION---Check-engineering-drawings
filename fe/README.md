# Frontend Application

This is a modern Next.js frontend application, built with React, TypeScript, Tailwind CSS, and shadcn/ui.

## Tech Stack
- **Framework:** [Next.js](https://nextjs.org/) (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** [shadcn/ui](https://ui.shadcn.com/) (Radix UI + Lucide Icons)
- **Package Manager:** `pnpm`

## Prerequisites
Before you begin, ensure you have the following installed on your local machine:
- **Node.js** (v18.17.0 or higher recommended)
- **pnpm** (Install via `npm install -g pnpm` if you don't have it)

## Getting Started

### 1. Install Dependencies
Navigate to the project root directory and install dependencies:

```bash
pnpm install
```

### 2. Run the Development Server
Start the development server on localhost:

```bash
pnpm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the application. The app supports Hot Module Replacement (HMR), so any changes you make will instantly update in the browser.

## Available Scripts

In the project directory, you can run the following commands:

- `pnpm run dev`: Starts the Next.js development server.
- `pnpm run build`: Builds the application for production usage.
- `pnpm run start`: Starts the Next.js production server (you must run `pnpm run build` beforehand).
- `pnpm run lint`: Runs ESLint to analyze the code and check for style/linting issues.

## Project Structure

A brief overview of the top-level directories:

- `/app`: Contains all Next.js App Router pages and layouts (`/login`, `/register`, `/admin`, `/account`, etc.).
- `/components`: Contains shared React components.
  - `/components/ui`: Houses reusable UI components scaffolded by `shadcn/ui`.
- `/lib`: Utility functions and shared library code (such as `utils.ts`).
- `/hooks`: Custom React hooks (like `use-toast.ts`, `use-mobile.ts`).
- `/public`: Static assets like images and fonts.

## UI Components (shadcn/ui)

This project uses `shadcn/ui` for its component library. The configuration is stored in `components.json`.

If you need to add a new `shadcn/ui` component into the project, you can use their CLI:

```bash
pnpm dlx shadcn@latest add <component-name>
```

For example, to add a dialog component:
```bash
pnpm dlx shadcn@latest add dialog
```